"""HTTP/SQL recovery evidence, preserving P01/P02 and new run histories."""

import argparse
import json
import tempfile
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from mock_api.app import FIXTURE
from scripts.api_capture import CaptureError
from scripts.business_load import load, sql
from scripts.check_api_capture import inspect_run
from scripts.check_api_failures import local_server
from scripts.check_business_load import preserved
from scripts.migration_config import TEST_DATABASE, test_engine
from scripts.reliable_capture import checkpoint, drive
from scripts.reprocess_rejection import recover


def assert_checkpoint(engine, report, page, records, complete):
    with engine.connect() as connection:
        cp = checkpoint(connection, report["capture_run_id"])
        stored = sql(
            connection,
            "SELECT count(*),coalesce(sum(item_count),0) FROM ilc.capture_pages WHERE run_id=:run",
            run=report["capture_run_id"],
        ).one()
        lineage = sql(
            connection,
            """SELECT count(*),count(DISTINCT a.input_key),count(DISTINCT a.receipt_key)
            FROM ilc.attempts a WHERE a.run_id=:run""",
            run=report["capture_run_id"],
        ).one()
        history = sql(
            connection,
            "SELECT count(*) FROM ilc.capture_checkpoint_history WHERE capture_run_id=:run",
            run=report["capture_run_id"],
        ).scalar_one()
        if (
            (cp["last_page"], cp["records"], cp["complete"])
            != (page, records, complete)
            or tuple(stored) != (page, records)
            or tuple(lineage) != (records, records, records)
            or history != page
        ):
            raise AssertionError(
                "Checkpoint is not reconciled with committed rows/history"
            )


def global_counts(connection):
    return tuple(
        sql(
            connection,
            """SELECT (SELECT count(*) FROM ilc.orders),
        (SELECT count(*) FROM ilc.deliveries),(SELECT count(*) FROM ilc.events)""",
        ).one()
    )


def run(engine, original_capture):
    with engine.connect() as connection:
        original_signature = preserved(connection, original_capture)
        domain_before = global_counts(connection)
    with local_server() as (base, pid):
        url = base + "/events"
        stopped = drive(engine, url, stop_after=1)
        if stopped["error_category"] != "SIMULATED_INTERRUPT_AFTER_COMMIT":
            raise AssertionError("Expected controlled interruption")
        assert_checkpoint(engine, stopped, 1, 5, False)
        rolled_back = drive(engine, url, stopped["capture_run_id"], fail_before=2)
        if rolled_back["error_category"] != "SIMULATED_BEFORE_COMMIT":
            raise AssertionError("Expected pre-commit rollback")
        assert_checkpoint(engine, rolled_back, 1, 5, False)
        resumed = drive(engine, url, stopped["capture_run_id"])
        if resumed["status"] != "SUCCEEDED":
            raise AssertionError("Resume did not complete")
        assert_checkpoint(engine, resumed, 3, 13, True)
        noop = drive(engine, url, stopped["capture_run_id"])
        if noop["requests"] != 0:
            raise AssertionError("Completed capture was fetched again")
        exhausted = drive(engine, url, scenario="http-503")
        if (
            exhausted["requests"] != 3
            or exhausted["error_category"] != "RETRY_EXHAUSTED:HTTP_503"
        ):
            raise AssertionError("Transient retry budget did not exhaust precisely")
        assert_checkpoint(engine, exhausted, 0, 0, False)
        timeout = drive(engine, url, scenario="delay", timeout=0.2)
        if (
            timeout["requests"] != 3
            or timeout["error_category"] != "RETRY_EXHAUSTED:ReadTimeout"
        ):
            raise AssertionError("Real read timeout retry budget did not exhaust")
        assert_checkpoint(engine, timeout, 0, 0, False)
        invalid = drive(engine, url, scenario="invalid-json")
        if invalid["requests"] != 1 or invalid["error_category"] != "INVALID_JSON":
            raise AssertionError("Invalid JSON retried or incorrectly accepted")
        snapshot = drive(engine, url, stop_after=1)
        with tempfile.TemporaryDirectory(prefix="ilc-p03-snapshot-") as directory:
            changed = Path(directory) / "changed.jsonl"
            lines = FIXTURE.read_text().splitlines()
            first = json.loads(lines[0])
            first["notes"] = "Different synthetic snapshot"
            lines[0] = json.dumps(first)
            changed.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with local_server(changed) as (other, _):
                mismatch = drive(engine, other + "/events", snapshot["capture_run_id"])
            if mismatch["error_category"] != "SNAPSHOT_CHANGED":
                raise AssertionError("Changed snapshot not refused")
            assert_checkpoint(engine, mismatch, 1, 5, False)
        snapshot_resumed = drive(engine, url, snapshot["capture_run_id"])
        assert_checkpoint(engine, snapshot_resumed, 3, 13, True)
    _, pages, events = inspect_run(engine, resumed["capture_run_id"])
    expected = sorted(
        [json.loads(line) for line in FIXTURE.read_text().splitlines()],
        key=lambda item: (item["source_system"], item["event_id"]),
    )
    if events != expected or len(pages) != 3:
        raise AssertionError("Resumed bytes did not recover all 13 records in order")
    business = load(engine, resumed["capture_run_id"])
    with engine.connect() as connection:
        if global_counts(connection) != domain_before or business.get("events") != {
            "DUPLICATE": 14,
            "CONFLICT": 1,
            "REJECTED": 3,
        }:
            raise AssertionError("Resumed inputs duplicated business entities")
    recovery = recover(engine)
    with engine.connect() as connection:
        after_recovery = global_counts(connection)
    recovery_again = recover(engine)
    with engine.connect() as connection:
        final = global_counts(connection)
        if final != after_recovery or original_signature != preserved(
            connection, original_capture
        ):
            raise AssertionError(
                "Recovery duplicated entities or modified P02 evidence/sentinel"
            )
        if (
            recovery_again["recovered_outcome"] != "DUPLICATE"
            or recovery_again["late_event_outcome"] != "DUPLICATE"
        ):
            raise AssertionError("Recovery reexecution not idempotent in domain")
        requests = [
            dict(row)
            for row in sql(
                connection,
                """SELECT page_number,request_attempt,http_status,error_category,
            encode(response_body,'escape') AS response_body FROM ilc.capture_request_log
            WHERE invocation_run_id=:run ORDER BY request_attempt""",
                run=exhausted["invocation_run_id"],
            ).mappings()
        ]
    return {
        "verification": "PASS",
        "http_children_stopped": True,
        "last_http_child_pid": pid,
        "after_commit_interrupt": stopped,
        "before_commit_rollback": rolled_back,
        "resume": resumed,
        "completed_noop": noop,
        "retry_exhaustion": exhausted,
        "retry_http_evidence": requests,
        "timeout_exhaustion": timeout,
        "json_without_retry": invalid,
        "snapshot_changed": mismatch,
        "snapshot_resume": snapshot_resumed,
        "business_reload": business,
        "reference_recovery": recovery,
        "recovery_reexecution": recovery_again,
        "domain_before_recovery": domain_before,
        "domain_after_recovery": after_recovery,
        "domain_after_reexecution": final,
        "original_capture_signature_preserved": original_signature,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--original-capture", required=True)
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        print(json.dumps(run(engine, args.original_capture), indent=2, default=str))
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (
        AssertionError,
        CaptureError,
        SQLAlchemyError,
        ValueError,
        RuntimeError,
        OSError,
    ) as exc:
        print(
            json.dumps(
                {
                    "verification": "FAIL",
                    "error_category": type(exc).__name__,
                    "detail": str(exc)
                    if isinstance(exc, (AssertionError, CaptureError))
                    else "Inspect database run state",
                }
            )
        )
        raise SystemExit(1) from None

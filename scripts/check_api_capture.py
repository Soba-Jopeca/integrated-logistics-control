"""Evidencia HTTP real + SELECTs do PostgreSQL; preserva os runs para auditoria."""

import argparse
import hashlib
import json

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from mock_api.app import FIXTURE
from scripts.api_capture import STAGE, CaptureError, capture
from scripts.check_api_failures import local_server
from scripts.migration_config import TEST_DATABASE, test_engine


def inspect_run(engine, run_id):
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        run = (
            connection.execute(
                text("""
            SELECT run_id,status,error_category,started_at,ended_at
            FROM ilc.runs WHERE run_id=:run AND stage=:stage
        """),
                {"run": run_id, "stage": STAGE},
            )
            .mappings()
            .one()
        )
        pages = (
            connection.execute(
                text("""
            SELECT page_key,page_number,response_body,response_sha256,item_count,
                   capture_status,http_status FROM ilc.capture_pages
            WHERE run_id=:run ORDER BY page_number
        """),
                {"run": run_id},
            )
            .mappings()
            .all()
        )
        items = []
        for page in pages:
            raw = bytes(page["response_body"])
            if hashlib.sha256(raw).hexdigest() != page["response_sha256"]:
                raise AssertionError("Stored bytes/checksum mismatch")
            payload = json.loads(raw)
            if page["capture_status"] == "CAPTURED":
                if len(payload["items"]) != page["item_count"]:
                    raise AssertionError("Page count mismatch")
                items.extend(payload["items"])
        mapped = connection.execute(
            text("""
            SELECT count(*) FROM ilc.capture_items c
            JOIN ilc.capture_pages p USING(page_key)
            JOIN ilc.inputs i USING(input_key)
            JOIN ilc.receipts r USING(input_key)
            JOIN ilc.attempts a ON a.input_key=i.input_key AND a.receipt_key=r.receipt_key
            WHERE p.run_id=:run AND a.run_id=:run
              AND i.original_sha256=p.response_sha256
              AND r.original_sha256=p.response_sha256
              AND i.received_at=p.received_at AND r.attempt_received_at=p.received_at
        """),
            {"run": run_id},
        ).scalar_one()
        if mapped != len(items):
            raise AssertionError("Provenance mapping mismatch")
    return dict(run), pages, items


def run(engine):
    with engine.connect() as connection:
        baseline = tuple(
            connection.execute(
                text("""
            SELECT (SELECT count(*) FROM ilc.orders),
                   (SELECT count(*) FROM ilc.deliveries),(SELECT count(*) FROM ilc.events)
        """)
            ).one()
        )
    with local_server() as (base_url, pid):
        good = capture(engine, base_url + "/events")
        bad = capture(engine, base_url + "/events", fail_http_after=1)
    good_run, good_pages, good_items = inspect_run(engine, good["run_id"])
    bad_run, bad_pages, bad_items = inspect_run(engine, bad["run_id"])
    records = [json.loads(line) for line in FIXTURE.read_text().splitlines() if line]
    expected = [
        item
        for _, item in sorted(
            enumerate(records),
            key=lambda pair: (pair[1]["source_system"], pair[1]["event_id"], pair[0]),
        )
    ]
    if (
        good["status"] != "SUCCEEDED"
        or good_run["status"] != "SUCCEEDED"
        or good_items != expected
        or len(good_items) != 13
        or [page["item_count"] for page in good_pages] != [5, 5, 3]
    ):
        raise AssertionError(
            "Successful capture did not reconcile with all fixture fields"
        )
    if (
        bad["status"] != "FAILED"
        or bad_run["status"] != "FAILED"
        or bad_run["error_category"] != "HTTP_ERROR"
        or bad_items != expected[:5]
        or len(bad_pages) != 2
        or bad_pages[-1]["http_status"] != 503
    ):
        raise AssertionError("Partial capture/failure evidence mismatch")
    with engine.connect() as connection:
        after = tuple(
            connection.execute(
                text("""
            SELECT (SELECT count(*) FROM ilc.orders),
                   (SELECT count(*) FROM ilc.deliveries),(SELECT count(*) FROM ilc.events)
        """)
            ).one()
        )
    if baseline != after:
        raise AssertionError("Business table counts changed during capture")
    return {
        "verification": "PASS",
        "child_pid": pid,
        "child_stopped": True,
        "successful_capture": good,
        "failed_capture": bad,
        "recovered_event_ids": [item["event_id"] for item in good_items],
        "all_fixture_fields_reconciled": True,
        "stored_http_error_body": bytes(bad_pages[-1]["response_body"]).decode(),
        "business_counts_before": baseline,
        "business_counts_after": after,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        print(json.dumps(run(engine), indent=2, default=str))
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (
        SQLAlchemyError,
        CaptureError,
        AssertionError,
        ValueError,
        RuntimeError,
        OSError,
    ) as exc:
        print(
            json.dumps({"verification": "FAIL", "error_category": type(exc).__name__})
        )
        raise SystemExit(1) from None

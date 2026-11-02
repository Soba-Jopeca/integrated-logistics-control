"""Carga/reexecucao e consultas SQL reconciliadas, sem apagar evidencias."""

import argparse
import hashlib
import json

from sqlalchemy.exc import SQLAlchemyError

from scripts.business_load import LoadError, encoded, load, sql, utc_text
from scripts.migration_config import TEST_DATABASE, test_engine


def inventory(connection):
    return tuple(
        sql(
            connection,
            """SELECT
        (SELECT count(*) FROM ilc.orders WHERE source_system='synthetic_reference'),
        (SELECT count(*) FROM ilc.deliveries d JOIN ilc.orders o USING(order_key) WHERE o.source_system='synthetic_reference'),
        (SELECT count(*) FROM ilc.events WHERE source_system='synthetic_events')""",
        ).one()
    )


def preserved(connection, capture_run):
    rows = (
        sql(
            connection,
            """SELECT i.*,p.response_sha256,p.page_key,c.item_index FROM ilc.inputs i
        JOIN ilc.capture_items c USING(input_key) JOIN ilc.capture_pages p USING(page_key)
        WHERE p.run_id=:run ORDER BY p.page_number,c.item_index""",
            run=capture_run,
        )
        .mappings()
        .all()
    )
    sentinel = (
        sql(
            connection,
            """SELECT row_to_json(o)::text FROM ilc.orders o WHERE source_system='__p02d_preservation__'
        UNION ALL SELECT row_to_json(d)::text FROM ilc.deliveries d WHERE delivery_id='P02D-SENTINEL'
        UNION ALL SELECT row_to_json(e)::text FROM ilc.events e WHERE source_system='__p02d_preservation__'""",
        )
        .scalars()
        .all()
    )
    return hashlib.sha256(
        json.dumps(
            [list(map(str, row.values())) for row in rows] + [sorted(sentinel)]
        ).encode()
    ).hexdigest()


def verify_run(connection, report, expected, reference_outcome="DUPLICATE"):
    if report.get("status") != "PARTIAL" or report.get("events") != expected:
        raise AssertionError("Unexpected event classification: " + encoded(report))
    expected_references = {
        kind: {reference_outcome: 8} for kind in ("orders", "deliveries")
    }
    if report.get("references") != expected_references:
        raise AssertionError("Reference rows did not reconcile")
    for body, checksum in sql(
        connection,
        "SELECT original_bytes,original_sha256 FROM ilc.reference_imports WHERE run_id=:run",
        run=report["run_id"],
    ):
        if hashlib.sha256(bytes(body)).hexdigest() != checksum:
            raise AssertionError("CSV bytes/checksum mismatch")
    persisted = dict(
        sql(
            connection,
            """SELECT p.outcome,count(*) FROM ilc.event_processing_results p
        JOIN ilc.attempts a USING(attempt_id,input_key) WHERE a.run_id=:run GROUP BY p.outcome""",
            run=report["run_id"],
        ).all()
    )
    if persisted != expected:
        raise AssertionError("SQL reconciliation differs from report")
    unknown = sql(
        connection,
        """SELECT count(*) FROM ilc.event_processing_results p
        JOIN ilc.attempts a USING(attempt_id,input_key)
        LEFT JOIN ilc.supplement_payloads s USING(input_key)
        WHERE a.run_id=:run AND p.outcome='REJECTED' AND s.input_key IS NULL""",
        run=report["run_id"],
    ).scalar_one()
    if unknown:
        raise AssertionError("Rejected content not recoverable")


def run(engine, capture_run):
    with engine.connect() as connection:
        before = inventory(connection)
        signature = preserved(connection, capture_run)
    if before not in ((0, 0, 0), (8, 8, 13)):
        raise AssertionError("Unexpected fixture state; preserve and investigate")
    first = load(engine, capture_run)
    second = load(engine, capture_run)
    unresolved = load(engine, capture_run, include_unresolved=True)
    with engine.connect() as connection:
        expected_first = (
            {"ACCEPTED": 13, "DUPLICATE": 1, "CONFLICT": 1, "REJECTED": 3}
            if before == (0, 0, 0)
            else {"DUPLICATE": 14, "CONFLICT": 1, "REJECTED": 3}
        )
        verify_run(
            connection,
            first,
            expected_first,
            "INSERTED" if before == (0, 0, 0) else "DUPLICATE",
        )
        verify_run(connection, second, {"DUPLICATE": 14, "CONFLICT": 1, "REJECTED": 3})
        verify_run(
            connection, unresolved, {"DUPLICATE": 14, "CONFLICT": 1, "REJECTED": 4}
        )
        after = inventory(connection)
        if after != (8, 8, 13) or signature != preserved(connection, capture_run):
            raise AssertionError("Entity counts or original inputs/sentinel changed")
        conflict_counts = dict(
            sql(
                connection,
                """SELECT c.conflict_type,count(DISTINCT c.conflict_key)
            FROM ilc.conflicts c JOIN ilc.conflict_evidence x USING(conflict_key)
            JOIN ilc.events e ON e.event_key=x.event_key
            WHERE e.source_system='synthetic_events' GROUP BY c.conflict_type""",
            ).all()
        )
        if conflict_counts != {"EVENT_IDENTITY": 1, "COMPLETION_AMBIGUITY": 2}:
            raise AssertionError(
                "Expected one identity and two completion conflict cases"
            )
        original = sql(
            connection,
            "SELECT occurred_at FROM ilc.events WHERE source_system='synthetic_events' AND event_id='EVT-IDENTITY'",
        ).scalar_one()
        if utc_text(original) != "2026-10-16T17:00:00.000000Z":
            raise AssertionError("Original event was overwritten")
        chosen = dict(
            sql(
                connection,
                """SELECT d.delivery_id,e.occurred_at
            FROM ilc.completion_decisions c JOIN ilc.deliveries d USING(delivery_key)
            JOIN ilc.events e ON e.event_key=c.event_key
            WHERE d.delivery_id IN ('ENT-003','ENT-004') AND c.decision_number=1""",
            ).all()
        )
        if {key: utc_text(value) for key, value in chosen.items()} != {
            "ENT-003": "2026-10-16T17:00:00.000000Z",
            "ENT-004": "2026-10-16T17:10:00.000000Z",
        }:
            raise AssertionError("Provisional conclusion ignored acceptance order")
        reasons = [
            dict(row)
            for row in sql(
                connection,
                """SELECT p.outcome,p.reason,count(*) AS count
            FROM ilc.event_processing_results p JOIN ilc.attempts a USING(attempt_id,input_key)
            WHERE a.run_id=:run GROUP BY p.outcome,p.reason ORDER BY p.outcome,p.reason""",
                run=unresolved["run_id"],
            ).mappings()
        ]
        if not any(
            row["reason"] == "INVALID_REFERENCE" and row["count"] == 1
            for row in reasons
        ):
            raise AssertionError("Unresolved reference not distinguished")
    return {
        "verification": "PASS",
        "before": before,
        "after": after,
        "first": first,
        "reexecution": second,
        "unresolved_case": unresolved,
        "conflict_cases": conflict_counts,
        "original_identity_event_preserved": True,
        "capture_inputs_and_sentinel_preserved": True,
        "rejection_reasons": reasons,
        "capture_input_signature": signature,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--capture-run", required=True)
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        print(json.dumps(run(engine, args.capture_run), indent=2, default=str))
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (SQLAlchemyError, LoadError, AssertionError, ValueError, OSError) as exc:
        print(
            json.dumps(
                {
                    "verification": "FAIL",
                    "error_category": type(exc).__name__,
                    "detail": str(exc)
                    if isinstance(exc, AssertionError)
                    else "Check stored run state; no credentials logged",
                }
            )
        )
        raise SystemExit(1) from None

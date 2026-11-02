"""Recover a preserved unknown reference; append attempts and retain rejection."""

from uuid import uuid4

from scripts.api_capture import now
from scripts.business_load import (
    ROOT,
    LoadError,
    process_event,
    references,
    sql,
    supplements,
    utc_text,
)


def completion(connection):
    return dict(
        sql(
            connection,
            """SELECT c.completion_decision_key,e.event_key,e.occurred_at
        FROM ilc.completion_decisions c JOIN ilc.events e USING(event_key)
        JOIN ilc.deliveries d ON d.delivery_key=c.delivery_key
        WHERE d.delivery_id='ENT-008' ORDER BY c.decision_number DESC LIMIT 1""",
        )
        .mappings()
        .one()
    )


def recover(engine):
    run_id = "reprocess-p03-" + str(uuid4())
    with engine.begin() as connection:
        sql(
            connection,
            "INSERT INTO ilc.runs(run_id,stage,started_at,status) VALUES (:run,'REFERENCE_RECOVERY_P03',:time,'RUNNING')",
            run=run_id,
            time=now(),
        )
    try:
        with engine.begin() as connection:
            sql(connection, "SET LOCAL lock_timeout='5s'")
            sql(connection, "SELECT pg_advisory_xact_lock(502002)")
            prior = (
                sql(
                    connection,
                    """SELECT p.attempt_id,p.input_key,p.normalized_payload,i.received_at
                FROM ilc.event_processing_results p JOIN ilc.attempts a USING(attempt_id,input_key)
                JOIN ilc.inputs i USING(input_key)
                WHERE p.reason='INVALID_REFERENCE' AND i.declared_id='UNRESOLVED-REFERENCE'
                ORDER BY a.started_at,a.attempt_id LIMIT 1""",
                )
                .mappings()
                .one()
            )
            refs = references(connection, run_id, ROOT / "tests/fixtures/reliability")
            if any(
                values.get("REJECTED", 0) or values.get("CONFLICT", 0)
                for values in refs.values()
            ):
                raise LoadError("RECOVERY_REFERENCE_NOT_ACCEPTED")
            result = process_event(
                connection, run_id, prior["input_key"], prior["normalized_payload"]
            )
            if result not in ("ACCEPTED", "DUPLICATE"):
                raise LoadError("RECOVERY_NOT_ACCEPTED")
            new_attempt = sql(
                connection,
                "SELECT attempt_id FROM ilc.attempts WHERE run_id=:run AND input_key=:input",
                run=run_id,
                input=prior["input_key"],
            ).scalar_one()
            sql(
                connection,
                "INSERT INTO ilc.reprocessing_links VALUES (:new,:previous,'REFERENCE_REGISTERED')",
                new=new_attempt,
                previous=prior["attempt_id"],
            )
            before = completion(connection)
            late_input, late_payload = supplements(
                connection, [ROOT / "tests/fixtures/reliability/late_event.jsonl"]
            )[0]
            late_outcome = process_event(connection, run_id, late_input, late_payload)
            after = completion(connection)
            if before != after or late_outcome not in ("ACCEPTED", "DUPLICATE"):
                raise LoadError("LATE_EVENT_REGRESSED_COMPLETION")
            original = sql(
                connection,
                "SELECT outcome FROM ilc.attempts WHERE attempt_id=:id",
                id=prior["attempt_id"],
            ).scalar_one()
            received = sql(
                connection,
                "SELECT received_at FROM ilc.inputs WHERE input_key=:input",
                input=prior["input_key"],
            ).scalar_one()
            receipt = sql(
                connection,
                "SELECT receipt_key FROM ilc.attempts WHERE attempt_id=:id",
                id=new_attempt,
            ).scalar_one()
            if (
                original != "REJECTED"
                or received != prior["received_at"]
                or receipt is not None
            ):
                raise LoadError("RECOVERY_REWROTE_HISTORY")
            sql(
                connection,
                "UPDATE ilc.runs SET status='SUCCEEDED',ended_at=:time WHERE run_id=:run",
                time=now(),
                run=run_id,
            )
        return {
            "run_id": run_id,
            "status": "SUCCEEDED",
            "recovered_outcome": result,
            "previous_attempt_id": str(prior["attempt_id"]),
            "new_attempt_id": str(new_attempt),
            "input_key": str(prior["input_key"]),
            "received_at_preserved": received.isoformat(),
            "original_rejection_preserved": True,
            "new_receipt_created": False,
            "late_event_outcome": late_outcome,
            "physical_state_before": "DELIVERED",
            "physical_state_after": "DELIVERED",
            "conclusion_at": utc_text(after["occurred_at"]),
            "late_occurred_at": late_payload["occurred_at"],
            "references": refs,
        }
    except Exception as exc:
        with engine.begin() as connection:
            sql(
                connection,
                "UPDATE ilc.runs SET status='FAILED',ended_at=:time,error_category=:error WHERE run_id=:run",
                time=now(),
                error=type(exc).__name__,
                run=run_id,
            )
        raise

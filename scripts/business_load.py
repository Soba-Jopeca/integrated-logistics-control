"""CSV references + preserved API events -> business entities with immutable results."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import UTC
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from mock_api.app import Event
from scripts.api_capture import now
from scripts.migration_config import TEST_DATABASE, test_engine

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/synthetic/v1"
CSV_ROOT = ROOT / "tests/fixtures/reference_csv/v1"
NORMALIZER = "event-business-v1"
STAGE = "BUSINESS_LOAD_P02B"


class LoadError(Exception):
    """Public error category, without SQL credentials."""


def sql(connection, statement, **params):
    return connection.execute(text(statement), params)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def utc_text(value):
    """Normaliza o horario para comparacao de identidade."""
    return (
        value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def normalize_event(payload):
    event = Event.model_validate(payload)
    data = event.model_dump(mode="json")
    data["occurred_at"] = utc_text(event.occurred_at)
    # model_dump inclui notes=None para tornar ausencia e null equivalentes.
    return data, digest(encoded(data).encode())


def timestamp(value):
    from datetime import datetime

    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timezone required")
    return utc_text(result.astimezone(UTC))


def references(connection, run_id):
    adapter = json.loads((CSV_ROOT / "adapter.json").read_text())
    totals = {"orders": Counter(), "deliveries": Counter()}
    sql(
        connection,
        "INSERT INTO ilc.sources VALUES ('synthetic_reference','Synthetic references') ON CONFLICT DO NOTHING",
    )
    for kind in ("orders", "deliveries"):
        raw = (CSV_ROOT / (kind + ".csv")).read_bytes()
        meta = adapter["files"][kind]
        source_raw = (ROOT / meta["source"]).read_bytes()
        if (
            digest(raw) != meta["csv_sha256"]
            or digest(source_raw) != meta["source_sha256"]
        ):
            raise LoadError("REFERENCE_CHECKSUM_MISMATCH")
        file_key = uuid4()
        sql(
            connection,
            """INSERT INTO ilc.reference_imports
            (file_key,run_id,source_system,kind,file_name,original_bytes,original_sha256,
             source_jsonl_sha256,adapter_version,received_at)
            VALUES (:key,:run,'synthetic_reference',:kind,:name,:raw,:sha,:source,:adapter,:received)""",
            key=file_key,
            run=run_id,
            kind="ORDER" if kind == "orders" else "DELIVERY",
            name=kind + ".csv",
            raw=raw,
            sha=digest(raw),
            source=meta["source_sha256"],
            adapter=adapter["adapter_version"],
            received=now(),
        )
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
        if len(rows) != meta["rows"]:
            raise LoadError("REFERENCE_ROW_COUNT_MISMATCH")
        for number, row in enumerate(rows, 1):
            outcome, reason, previous, entity = "INSERTED", None, None, None
            incoming = dict(row)
            try:
                if kind == "orders":
                    incoming = {
                        "source_system": row["source_system"],
                        "order_id": row["order_id"],
                        "released_at": timestamp(row["released_at"]),
                        "request_data": json.loads(row["request_data"]),
                    }
                    if incoming[
                        "source_system"
                    ] != "synthetic_reference" or not isinstance(
                        incoming["request_data"], dict
                    ):
                        raise ValueError("Invalid reference source/request")
                    existing = (
                        sql(
                            connection,
                            "SELECT * FROM ilc.orders WHERE source_system=:source AND order_id=:id FOR UPDATE",
                            source=incoming["source_system"],
                            id=incoming["order_id"],
                        )
                        .mappings()
                        .one_or_none()
                    )
                    if existing:
                        entity = existing["order_key"]
                        previous = {
                            "source_system": existing["source_system"],
                            "order_id": existing["order_id"],
                            "released_at": utc_text(existing["released_at"]),
                            "request_data": existing["request_data"],
                        }
                    else:
                        entity = uuid4()
                        sql(
                            connection,
                            """INSERT INTO ilc.orders(order_key,source_system,order_id,released_at,request_data)
                            VALUES (:key,:source,:id,:released,CAST(:data AS jsonb))""",
                            key=entity,
                            source=incoming["source_system"],
                            id=incoming["order_id"],
                            released=incoming["released_at"],
                            data=encoded(incoming["request_data"]),
                        )
                else:
                    quantity = int(row["expected_quantity"])
                    incoming = {
                        "delivery_id": row["delivery_id"],
                        "order_source_system": row["order_source_system"],
                        "order_id": row["order_id"],
                        "promised_at": timestamp(row["promised_at"])
                        if row["promised_at"]
                        else None,
                        "expected_quantity": quantity,
                        "quantity_unit": row["quantity_unit"],
                    }
                    if (
                        quantity < 0
                        or not incoming["quantity_unit"]
                        or incoming["quantity_unit"]
                        != incoming["quantity_unit"].strip()
                    ):
                        raise ValueError("Invalid quantity/unit")
                    order = sql(
                        connection,
                        "SELECT order_key FROM ilc.orders WHERE source_system=:source AND order_id=:id",
                        source=row["order_source_system"],
                        id=row["order_id"],
                    ).scalar_one_or_none()
                    if order is None:
                        raise ValueError("INVALID_REFERENCE")
                    existing = (
                        sql(
                            connection,
                            """SELECT d.*,o.source_system,o.order_id FROM ilc.deliveries d
                        JOIN ilc.orders o USING(order_key) WHERE delivery_id=:id FOR UPDATE OF d""",
                            id=row["delivery_id"],
                        )
                        .mappings()
                        .one_or_none()
                    )
                    if existing:
                        entity = existing["delivery_key"]
                        previous = {
                            "delivery_id": existing["delivery_id"],
                            "order_source_system": existing["source_system"],
                            "order_id": existing["order_id"],
                            "promised_at": utc_text(existing["promised_at"])
                            if existing["promised_at"]
                            else None,
                            "expected_quantity": existing["expected_quantity"],
                            "quantity_unit": existing["quantity_unit"],
                        }
                    else:
                        entity = uuid4()
                        sql(
                            connection,
                            """INSERT INTO ilc.deliveries(delivery_key,order_key,delivery_id,promised_at,expected_quantity,quantity_unit)
                            VALUES (:key,:order,:id,:promised,:quantity,:unit)""",
                            key=entity,
                            order=order,
                            id=incoming["delivery_id"],
                            promised=incoming["promised_at"],
                            quantity=quantity,
                            unit=incoming["quantity_unit"],
                        )
                if previous is not None:
                    outcome = "DUPLICATE" if incoming == previous else "CONFLICT"
                    reason = (
                        "IDENTICAL_REFERENCE"
                        if outcome == "DUPLICATE"
                        else "REFERENCE_IDENTITY_CONFLICT"
                    )
            except (ValueError, KeyError, TypeError):
                outcome, reason = "REJECTED", "INVALID_REFERENCE_ROW"
            totals[kind][outcome] += 1
            sql(
                connection,
                """INSERT INTO ilc.reference_results
                (file_key,row_number,outcome,reason,incoming_data,previous_data,entity_key)
                VALUES (:file,:number,:outcome,:reason,CAST(:incoming AS jsonb),CAST(:previous AS jsonb),:entity)""",
                file=file_key,
                number=number,
                outcome=outcome,
                reason=reason,
                incoming=encoded(incoming),
                previous=encoded(previous) if previous is not None else None,
                entity=entity,
            )
    return {kind: dict(values) for kind, values in totals.items()}


def captured_inputs(connection, capture_run):
    run = sql(
        connection,
        "SELECT status,stage FROM ilc.runs WHERE run_id=:run",
        run=capture_run,
    ).one_or_none()
    if run is None or tuple(run) != ("SUCCEEDED", "API_CAPTURE_P02A"):
        raise LoadError("CAPTURE_RUN_NOT_ACCEPTABLE")
    pages = (
        sql(
            connection,
            "SELECT * FROM ilc.capture_pages WHERE run_id=:run ORDER BY page_number",
            run=capture_run,
        )
        .mappings()
        .all()
    )
    by_id = {}
    for page in pages:
        raw = bytes(page["response_body"])
        if (
            page["capture_status"] != "CAPTURED"
            or digest(raw) != page["response_sha256"]
        ):
            raise LoadError("CAPTURE_BYTES_MISMATCH")
        items = json.loads(raw)["items"]
        links = dict(
            sql(
                connection,
                "SELECT item_index,input_key FROM ilc.capture_items WHERE page_key=:key",
                key=page["page_key"],
            ).all()
        )
        if len(links) != len(items):
            raise LoadError("CAPTURE_LINK_MISMATCH")
        for index, item in enumerate(items):
            identity = (item["source_system"], item["event_id"])
            if identity in by_id:
                raise LoadError("AMBIGUOUS_CAPTURE_IDENTITY")
            by_id[identity] = (links[index], item)
    expected = [
        json.loads(line)
        for line in (FIXTURES / "valid/events.jsonl").read_bytes().splitlines()
    ]
    if len(by_id) != 13:
        raise LoadError("EXPECTED_FIXTURE_13")
    ordered = []
    for line in (FIXTURES / "arrival_plan.jsonl").read_bytes().splitlines():
        arrival = json.loads(line)
        if arrival["payload"]["path"] != "valid/events.jsonl":
            continue
        item = expected[arrival["payload"]["line"] - 1]
        entry = by_id[(item["source_system"], item["event_id"])]
        if entry[1] != item:
            raise LoadError("CAPTURE_FIXTURE_CONTENT_MISMATCH")
        ordered.append(entry)
    return ordered


def supplements(connection, files=None):
    entries = []
    paths = (
        files
        if files is not None
        else [
            FIXTURES / name
            for name in (
                "replays/events.jsonl",
                "anomalies/events.jsonl",
                "invalid/events.jsonl",
            )
        ]
    )
    for path in paths:
        name = str(path.relative_to(ROOT))
        raw = path.read_bytes()
        for number, line in enumerate(raw.splitlines(keepends=True), 1):
            payload = json.loads(line)
            key, receipt = uuid4(), uuid4()
            received = now()
            reference = "pg:ilc.supplement_payloads/" + str(key)
            sql(
                connection,
                """INSERT INTO ilc.inputs(input_key,source_system,input_type,declared_id,
                original_reference,original_sha256,received_at,normalization_error)
                VALUES (:key,'synthetic_events','EVENT',:id,:reference,:sha,:received,'P02B_DERIVED_RESULT_PENDING')""",
                key=key,
                id=payload.get("event_id"),
                reference=reference,
                sha=digest(line),
                received=received,
            )
            sql(
                connection,
                """INSERT INTO ilc.receipts(receipt_key,input_key,attempt_received_at,original_reference,original_sha256)
                VALUES (:receipt,:key,:received,:reference,:sha)""",
                receipt=receipt,
                key=key,
                received=received,
                reference=reference,
                sha=digest(line),
            )
            sql(
                connection,
                """INSERT INTO ilc.supplement_payloads(input_key,file_name,file_sha256,line_number,original_bytes)
                VALUES (:key,:name,:sha,:number,:raw)""",
                key=key,
                name=name,
                sha=digest(raw),
                number=number,
                raw=line,
            )
            entries.append((key, payload))
    return entries


def event_content(connection, event):
    delivery_id = sql(
        connection,
        "SELECT delivery_id FROM ilc.deliveries WHERE delivery_key=:key",
        key=event["delivery_key"],
    ).scalar_one()
    return normalize_event(
        {
            "schema_version": event["schema_version"],
            "source_system": event["source_system"],
            "event_id": event["event_id"],
            "delivery_id": delivery_id,
            "event_type": event["event_type"],
            "occurred_at": event["occurred_at"],
            "notes": event["notes"],
        }
    )


def open_conflict(
    connection,
    kind,
    delivery,
    original,
    alternative_input,
    alternative_event=None,
    norm_hash=None,
):
    # Reenvio da mesma alternativa nao abre outro caso nem altera evidencia selada.
    existing = sql(
        connection,
        """SELECT c.conflict_key FROM ilc.conflicts c
        JOIN ilc.conflict_evidence o ON o.conflict_key=c.conflict_key AND o.evidence_role='ORIGINAL'
        JOIN ilc.conflict_evidence a ON a.conflict_key=c.conflict_key AND a.evidence_role='ALTERNATIVE'
        WHERE c.conflict_type=:kind AND o.event_key=:original
          AND ((CAST(:alternative AS uuid) IS NOT NULL AND a.event_key=CAST(:alternative AS uuid))
           OR (CAST(:hash AS text) IS NOT NULL AND EXISTS (SELECT 1 FROM ilc.event_processing_results p
               WHERE p.input_key=a.input_key AND p.normalized_sha256=CAST(:hash AS text))))
        LIMIT 1""",
        kind=kind,
        original=original["event_key"],
        alternative=alternative_event,
        hash=norm_hash,
    ).scalar_one_or_none()
    if existing:
        return existing
    key, opened = uuid4(), now()
    sql(
        connection,
        """INSERT INTO ilc.conflicts VALUES (:key,:delivery,:kind,:opened,:reason)""",
        key=key,
        delivery=delivery,
        kind=kind,
        opened=opened,
        reason=kind,
    )
    for input_key, event_key, role in (
        (original["input_key"], original["event_key"], "ORIGINAL"),
        (alternative_input, alternative_event, "ALTERNATIVE"),
    ):
        sql(
            connection,
            """INSERT INTO ilc.conflict_evidence
            (conflict_evidence_key,conflict_key,input_key,event_key,evidence_role,recorded_at)
            VALUES (:key,:conflict,:input,:event,:role,:time)""",
            key=uuid4(),
            conflict=key,
            input=input_key,
            event=event_key,
            role=role,
            time=opened,
        )
    return key


def process_event(connection, run_id, input_key, payload):
    attempt = uuid4()
    started = now()
    outcome, reason, event_key, conflict_key = "ACCEPTED", None, None, None
    normalized = norm_hash = None
    try:
        normalized, norm_hash = normalize_event(payload)
    except ValidationError as exc:
        error = exc.errors(include_url=False, include_input=False)[0]
        reason = (
            "MISSING_REQUIRED_FIELD"
            if error["type"] == "missing"
            else "INVALID_EVENT_CONTRACT"
        )
        outcome = "REJECTED"
    if normalized is not None:
        delivery = sql(
            connection,
            "SELECT delivery_key FROM ilc.deliveries WHERE delivery_id=:id FOR UPDATE",
            id=normalized["delivery_id"],
        ).scalar_one_or_none()
        existing = (
            sql(
                connection,
                "SELECT * FROM ilc.events WHERE source_system=:source AND event_id=:id",
                source=normalized["source_system"],
                id=normalized["event_id"],
            )
            .mappings()
            .one_or_none()
        )
        if existing:
            event_key = existing["event_key"]
            _, old_hash = event_content(connection, existing)
            if old_hash == norm_hash:
                outcome, reason = "DUPLICATE", "IDENTICAL_NORMALIZED_CONTENT"
            else:
                outcome, reason = "CONFLICT", "IDENTITY_CONFLICT"
                conflict_key = open_conflict(
                    connection,
                    "EVENT_IDENTITY",
                    existing["delivery_key"],
                    existing,
                    input_key,
                    norm_hash=norm_hash,
                )
        elif delivery is None:
            outcome, reason = "REJECTED", "INVALID_REFERENCE"
    # Tentativa interna nao inventa novo receipt nem muda received_at.
    sql(
        connection,
        """INSERT INTO ilc.attempts(attempt_id,input_key,run_id,started_at,ended_at,outcome,error_category)
        VALUES (:attempt,:input,:run,:start,:end,:outcome,:reason)""",
        attempt=attempt,
        input=input_key,
        run=run_id,
        start=started,
        end=now(),
        outcome=outcome,
        reason=reason,
    )
    if outcome == "ACCEPTED":
        event_key = uuid4()
        sequence = sql(
            connection,
            "SELECT coalesce(max(acceptance_sequence),0)+1 FROM ilc.events WHERE delivery_key=:delivery",
            delivery=delivery,
        ).scalar_one()
        sql(
            connection,
            """INSERT INTO ilc.events(event_key,source_system,event_id,delivery_key,schema_version,event_type,
            occurred_at,notes,input_key,accepted_attempt_id,accepted_at,acceptance_sequence)
            VALUES (:key,:source,:id,:delivery,:schema,:type,:occurred,:notes,:input,:attempt,:accepted,:sequence)""",
            key=event_key,
            source=normalized["source_system"],
            id=normalized["event_id"],
            delivery=delivery,
            schema=normalized["schema_version"],
            type=normalized["event_type"],
            occurred=normalized["occurred_at"],
            notes=normalized["notes"],
            input=input_key,
            attempt=attempt,
            accepted=now(),
            sequence=sequence,
        )
        if normalized["event_type"] == "DELIVERED":
            chosen = (
                sql(
                    connection,
                    """SELECT e.* FROM ilc.completion_decisions d JOIN ilc.events e USING(event_key)
                WHERE d.delivery_key=:delivery ORDER BY d.decision_number DESC LIMIT 1""",
                    delivery=delivery,
                )
                .mappings()
                .one_or_none()
            )
            if chosen is None:
                sql(
                    connection,
                    """INSERT INTO ilc.completion_decisions
                    (completion_decision_key,delivery_key,event_key,decision_number,decided_at,decision_type,author,reason)
                    VALUES (:key,:delivery,:event,1,:time,'PROVISIONAL','system:p02b','FIRST_ACCEPTED_DELIVERED')""",
                    key=uuid4(),
                    delivery=delivery,
                    event=event_key,
                    time=now(),
                )
            elif utc_text(chosen["occurred_at"]) != normalized["occurred_at"]:
                conflict_key = open_conflict(
                    connection,
                    "COMPLETION_AMBIGUITY",
                    delivery,
                    chosen,
                    input_key,
                    alternative_event=event_key,
                )
    sql(
        connection,
        """INSERT INTO ilc.event_processing_results
        (attempt_id,input_key,outcome,reason,normalizer_version,normalized_sha256,normalized_payload,event_key,conflict_key)
        VALUES (:attempt,:input,:outcome,:reason,:version,:sha,CAST(:data AS jsonb),:event,:conflict)""",
        attempt=attempt,
        input=input_key,
        outcome=outcome,
        reason=reason,
        version=NORMALIZER,
        sha=norm_hash,
        data=encoded(normalized) if normalized is not None else None,
        event=event_key,
        conflict=conflict_key,
    )
    return outcome


def load(engine, capture_run, include_unresolved=False):
    run_id = "business-" + str(uuid4())
    with engine.begin() as connection:
        if tuple(sql(connection, "SELECT current_database(),current_user").one()) != (
            TEST_DATABASE,
            "ilc_app",
        ):
            raise LoadError("WRONG_DATABASE")
        if (
            sql(
                connection, "SELECT version_num FROM public.alembic_version"
            ).scalar_one()
            != "0005_business_processing"
        ):
            raise LoadError("WRONG_REVISION")
        sql(
            connection,
            "INSERT INTO ilc.runs(run_id,stage,started_at,status) VALUES (:run,:stage,:time,'RUNNING')",
            run=run_id,
            stage=STAGE,
            time=now(),
        )
    try:
        with engine.begin() as connection:
            # Transacao unica e exclusao entre cargas deste recorte; sem retry.
            sql(connection, "SET LOCAL lock_timeout = '5s'")
            sql(connection, "SELECT pg_advisory_xact_lock(502002)")
            entries = captured_inputs(connection, capture_run)
            refs = references(connection, run_id)
            entries += supplements(connection)
            if include_unresolved:
                entries += supplements(
                    connection,
                    [ROOT / "tests/fixtures/business_cases/unresolved_event.jsonl"],
                )
            for input_key, payload in entries:
                process_event(connection, run_id, input_key, payload)
            result = dict(
                sql(
                    connection,
                    """SELECT p.outcome,count(*) FROM ilc.event_processing_results p
                JOIN ilc.attempts a USING(attempt_id,input_key) WHERE a.run_id=:run GROUP BY p.outcome""",
                    run=run_id,
                ).all()
            )
            if sum(result.values()) != len(entries):
                raise LoadError("RECONCILIATION_FAILED")
            issues = (
                result.get("CONFLICT", 0)
                + result.get("REJECTED", 0)
                + sum(
                    v.get("CONFLICT", 0) + v.get("REJECTED", 0) for v in refs.values()
                )
            )
            status = "PARTIAL" if issues else "SUCCEEDED"
            sql(
                connection,
                "UPDATE ilc.runs SET status=:status,ended_at=:time,error_category=:error WHERE run_id=:run",
                status=status,
                time=now(),
                error="DATA_QUALITY_ISSUES" if issues else None,
                run=run_id,
            )
        return {
            "run_id": run_id,
            "capture_run_id": capture_run,
            "status": status,
            "references": refs,
            "event_inputs": len(entries),
            "events": result,
        }
    except (SQLAlchemyError, LoadError, ValueError, KeyError, TypeError) as exc:
        with engine.begin() as connection:
            sql(
                connection,
                "UPDATE ilc.runs SET status='FAILED',ended_at=:time,error_category=:error WHERE run_id=:run",
                time=now(),
                error=type(exc).__name__,
                run=run_id,
            )
        return {
            "run_id": run_id,
            "status": "FAILED",
            "error_category": str(exc)
            if isinstance(exc, LoadError)
            else type(exc).__name__,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--capture-run", required=True)
    parser.add_argument("--include-unresolved-case", action="store_true")
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        report = load(
            engine, args.capture_run, include_unresolved=args.include_unresolved_case
        )
        print(json.dumps(report, default=str, indent=2))
        return (
            1
            if report["status"] == "FAILED"
            else 2
            if report["status"] == "PARTIAL"
            else 0
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SQLAlchemyError, LoadError, ValueError, OSError) as exc:
        print(json.dumps({"status": "FAILED", "error_category": type(exc).__name__}))
        raise SystemExit(1) from None

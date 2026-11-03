"""Versioned deterministic evaluation; no mutation of physical events/decisions."""

from datetime import UTC, datetime
from uuid import uuid4

from src.documents.parser import FIELDS, DocumentError
from src.documents.service import sql

RULES_VERSION = "document-rules-v1"


def same_utc_minute(actual, expected):
    """Joao implements this central comparison before database execution."""
    raise DocumentError("AUTHOR_COMPARISON_PENDING")


def reasons_for(
    extraction, delivery, completion, contested=False, identity_conflict=False
):
    reasons = []

    def add(code, field, detail):
        reasons.append({"code": code, "field": field, "detail": detail})

    if delivery is None:
        add("INVALID_REFERENCE", "declared_delivery_id", "REFERENCE_NOT_RESOLVED")
        return reasons
    if extraction is None or extraction["outcome"] != "EXTRACTED":
        add(
            "PARSING_ERROR",
            None,
            "NO_EXTRACTION" if extraction is None else extraction["error_category"],
        )
    else:
        for field in FIELDS:
            if extraction[field] is None or (
                isinstance(extraction[field], str) and not extraction[field].strip()
            ):
                add("MISSING_REQUIRED_FIELD", field, "ABSENT_IN_DOCUMENT")
        if (
            extraction["declared_delivery_id"] is not None
            and extraction["declared_delivery_id"] != delivery["delivery_id"]
        ):
            add(
                "REFERENCE_MISMATCH",
                "declared_delivery_id",
                "DECLARED_REFERENCE_DIFFERS",
            )
        for field, expected in [
            ("received_quantity", delivery["expected_quantity"]),
            ("quantity_unit", delivery["quantity_unit"]),
        ]:
            if extraction[field] is not None and extraction[field] != expected:
                add("VALUE_MISMATCH", field, "VALUE_DIFFERS")
        if (
            completion
            and not contested
            and extraction["delivered_at"] is not None
            and not same_utc_minute(
                extraction["delivered_at"], completion["occurred_at"]
            )
        ):
            add("VALUE_MISMATCH", "delivered_at", "UTC_MINUTE_DIFFERS")
    if completion is None:
        add("DELIVERY_NOT_CONFIRMED", "delivered_at", "NO_ELIGIBLE_COMPLETION")
    elif contested:
        add("DELIVERY_NOT_CONFIRMED", "delivered_at", "COMPLETION_CONTESTED")
    if identity_conflict:
        add("IDENTITY_CONFLICT", None, "OPEN_IDENTITY_CONFLICT")
    return reasons


def completion_context(c, delivery_key):
    completion = (
        sql(
            c,
            """SELECT e.event_key,e.occurred_at FROM ilc.completion_decisions d
        JOIN ilc.events e ON e.event_key=d.event_key
        WHERE d.delivery_key=:key ORDER BY d.decision_number DESC LIMIT 1""",
            key=delivery_key,
        )
        .mappings()
        .first()
    )
    conflicts = (
        sql(
            c,
            """SELECT conflict_type FROM ilc.conflicts f WHERE f.delivery_key=:key
        AND NOT EXISTS (SELECT 1 FROM ilc.conflict_resolutions r WHERE r.conflict_key=f.conflict_key)""",
            key=delivery_key,
        )
        .scalars()
        .all()
    )
    # Conservative: any unresolved delivery conflict blocks approval.
    contested = any(x != "DOCUMENT_IDENTITY" for x in conflicts)
    return completion, contested


def has_identity_conflict(c, doc):
    # P01 preserves rejected arrivals as inputs/attempts, not conflict aggregates.
    return sql(
        c,
        """SELECT EXISTS(SELECT 1 FROM ilc.inputs i JOIN ilc.attempts a USING(input_key)
        WHERE i.source_system=:source AND i.declared_id=:id AND i.input_type='DOCUMENT'
        AND a.error_category='IDENTITY_CONFLICT')""",
        source=doc["source_system"],
        id=doc["document_id"],
    ).scalar_one()


def evaluate(engine, document_key):
    with engine.begin() as c:
        sql(c, "SELECT pg_advisory_xact_lock(4040101)")
        doc = (
            sql(
                c,
                "SELECT * FROM ilc.document_versions WHERE document_key=:key",
                key=document_key,
            )
            .mappings()
            .one()
        )
        # Serialize against event ingestion which locks the same delivery row.
        delivery = (
            sql(
                c,
                "SELECT * FROM ilc.deliveries WHERE delivery_key=:key FOR UPDATE",
                key=doc["delivery_key"],
            )
            .mappings()
            .one()
        )
        now = datetime.now(UTC)
        extraction = (
            sql(
                c,
                """SELECT x.* FROM ilc.extractions x JOIN ilc.attempts a USING(attempt_id,input_key)
            JOIN ilc.runs r USING(run_id) WHERE x.document_key=:key
            ORDER BY r.started_at DESC,x.extracted_at DESC,x.extraction_key DESC LIMIT 1""",
                key=document_key,
            )
            .mappings()
            .first()
        )
        completion, contested = completion_context(c, doc["delivery_key"])
        identity_conflict = sql(
            c,
            """SELECT EXISTS(SELECT 1 FROM ilc.conflict_evidence e
            JOIN ilc.conflicts f USING(conflict_key) WHERE e.document_key=:doc
            AND NOT EXISTS(SELECT 1 FROM ilc.conflict_resolutions r WHERE r.conflict_key=f.conflict_key))""",
            doc=document_key,
        ).scalar_one()
        reasons = reasons_for(
            extraction,
            delivery,
            completion,
            contested,
            identity_conflict or has_identity_conflict(c, doc),
        )
        previous = (
            sql(
                c,
                "SELECT * FROM ilc.evaluations WHERE document_key=:key ORDER BY evaluation_number DESC LIMIT 1",
                key=document_key,
            )
            .mappings()
            .first()
        )
        number = previous["evaluation_number"] + 1 if previous else 1
        result = "REVIEW_REQUIRED" if reasons else "APPROVED"
        run, attempt, evaluation = "evaluation-" + str(uuid4()), uuid4(), uuid4()
        sql(
            c,
            "INSERT INTO ilc.runs VALUES (:run,'DOCUMENT_EVALUATION_P02',:now,:now,'SUCCEEDED',NULL)",
            run=run,
            now=now,
        )
        sql(
            c,
            "INSERT INTO ilc.attempts VALUES (:key,:input,:run,NULL,:now,:now,'ACCEPTED',NULL)",
            key=attempt,
            input=doc["input_key"],
            run=run,
            now=now,
        )
        sql(
            c,
            """INSERT INTO ilc.evaluations
            (evaluation_key,document_key,input_key,delivery_key,attempt_id,extraction_key,completion_event_key,
             evaluation_number,previous_evaluation_key,previous_evaluation_number,result,rules_version,evaluated_at,
             expected_quantity,expected_quantity_unit,expected_delivered_at)
            VALUES (:key,:doc,:input,:delivery,:attempt,:extraction,:event,:number,:previous,:previous_number,
            :result,:rules,:now,:quantity,:unit,:time)""",
            key=evaluation,
            doc=document_key,
            input=doc["input_key"],
            delivery=doc["delivery_key"],
            attempt=attempt,
            extraction=extraction["extraction_key"] if extraction else None,
            event=completion["event_key"] if completion else None,
            number=number,
            previous=previous["evaluation_key"] if previous else None,
            previous_number=previous["evaluation_number"] if previous else None,
            result=result,
            rules=RULES_VERSION,
            now=now,
            quantity=delivery["expected_quantity"],
            unit=delivery["quantity_unit"],
            time=completion["occurred_at"] if completion else None,
        )
        for reason in reasons:
            sql(
                c,
                "INSERT INTO ilc.evaluation_reasons VALUES (:key,:evaluation,:code,:field,:detail)",
                key=uuid4(),
                evaluation=evaluation,
                **reason,
            )
        sql(
            c,
            "UPDATE ilc.evaluation_validities SET valid_to=:now WHERE document_key=:doc AND valid_to IS NULL",
            now=now,
            doc=document_key,
        )
        sql(
            c,
            "INSERT INTO ilc.evaluation_validities VALUES (:key,:doc,:evaluation,:now,NULL)",
            key=uuid4(),
            doc=document_key,
            evaluation=evaluation,
            now=now,
        )
        return {
            "run_id": run,
            "document_key": str(document_key),
            "evaluation_key": str(evaluation),
            "number": number,
            "result": result,
            "reasons": reasons,
            "rules_version": RULES_VERSION,
        }


def regularity(engine, delivery_id):
    with engine.begin() as c:
        sql(c, "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        delivery = sql(
            c,
            "SELECT delivery_key FROM ilc.deliveries WHERE delivery_id=:id",
            id=delivery_id,
        ).scalar_one()
        completion, contested = completion_context(c, delivery)
        rows = (
            sql(
                c,
                """SELECT d.source_system,d.document_id,d.document_key,e.result,e.extraction_key,
            latest.extraction_key AS latest_extraction FROM ilc.document_versions d
            JOIN ilc.document_validities v USING(document_key)
            LEFT JOIN ilc.evaluation_validities ev ON ev.document_key=d.document_key AND ev.valid_to IS NULL
            LEFT JOIN ilc.evaluations e USING(evaluation_key)
            LEFT JOIN LATERAL (SELECT x.extraction_key FROM ilc.extractions x
                JOIN ilc.attempts a USING(attempt_id,input_key) JOIN ilc.runs r USING(run_id)
                WHERE x.document_key=d.document_key ORDER BY r.started_at DESC,x.extracted_at DESC,x.extraction_key DESC LIMIT 1) latest ON true
            WHERE d.delivery_key=:key AND v.valid_to IS NULL""",
                key=delivery,
            )
            .mappings()
            .all()
        )
        approved = sum(
            r["result"] == "APPROVED"
            and r["extraction_key"] == r["latest_extraction"]
            and not has_identity_conflict(c, r)
            for r in rows
        )
        pending = len(rows) - approved
        document_conflict = sql(
            c,
            """SELECT EXISTS(SELECT 1 FROM ilc.conflict_evidence ce
            JOIN ilc.document_validities v ON v.document_key=ce.document_key AND v.valid_to IS NULL
            JOIN ilc.conflicts f USING(conflict_key) WHERE f.delivery_key=:key
            AND NOT EXISTS(SELECT 1 FROM ilc.conflict_resolutions cr WHERE cr.conflict_key=f.conflict_key))""",
            key=delivery,
        ).scalar_one()
        return {
            "delivery_id": delivery_id,
            "physical_state": "DELIVERED" if completion else "NOT_CONFIRMED",
            "completion_contested": contested,
            "current_documents": len(rows),
            "approved": approved,
            "pending": pending,
            "regular": bool(
                approved
                and not pending
                and completion
                and not contested
                and not document_conflict
            ),
        }

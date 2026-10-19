"""Fingerprint all fifteen prior tables; seed a dedicated documentary sentinel."""

import argparse
import hashlib
import json
import sys
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from scripts.inspect_migration import CORE_TABLES, DOCUMENT_TABLES
from scripts.migration_config import TEST_DATABASE, test_engine

SOURCE = "__p02d_preservation__"


def sentinel_key(label):
    return str(uuid5(NAMESPACE_URL, SOURCE + "/" + label))


def initialize(connection):
    existing = connection.execute(text("SELECT description FROM ilc.sources WHERE source_system=:source"), {"source": SOURCE}).scalar_one_or_none()
    if existing is not None:
        raise RuntimeError("Sentinel already exists; inspect without --initialize")
    params = {name: sentinel_key(name) for name in (
        "order", "delivery", "input_event", "input_document", "receipt_event",
        "receipt_document", "attempt_event", "attempt_document", "event", "family",
        "document", "extraction", "evaluation", "reason", "doc_validity", "eval_validity",
    )}
    params["source"] = SOURCE
    statements = [
        "INSERT INTO ilc.sources VALUES (:source, 'Synthetic P02D preservation sentinel')",
        "INSERT INTO ilc.runs VALUES (:source, 'sentinel', '2026-10-19T10:00:00Z', '2026-10-19T10:01:00Z', 'SUCCEEDED', NULL)",
        "INSERT INTO ilc.orders VALUES (:order, :source, 'P02D-SENTINEL', '2026-10-19T09:00:00Z', '{}')",
        "INSERT INTO ilc.deliveries VALUES (:delivery, :order, 'P02D-SENTINEL', NULL, 10, 'VOLUME')",
    ]
    for kind in ("event", "document"):
        statements += [
            f"INSERT INTO ilc.inputs (input_key, source_system, input_type, original_reference, original_sha256, received_at, normalized_sha256, normalizer_version) VALUES (:input_{kind}, :source, '{kind.upper()}', 'synthetic://p02d-sentinel', repeat('a',64), '2026-10-19T10:00:00Z', repeat('a',64), 'sentinel-v1')",
            f"INSERT INTO ilc.receipts VALUES (:receipt_{kind}, :input_{kind}, '2026-10-19T10:00:00Z', 'synthetic://p02d-sentinel', repeat('a',64))",
            f"INSERT INTO ilc.attempts (attempt_id, input_key, run_id, receipt_key, started_at, ended_at, outcome) VALUES (:attempt_{kind}, :input_{kind}, :source, :receipt_{kind}, '2026-10-19T10:00:00Z', '2026-10-19T10:01:00Z', 'ACCEPTED')",
        ]
    statements += [
        "INSERT INTO ilc.events (event_key, source_system, event_id, delivery_key, schema_version, event_type, occurred_at, input_key, accepted_attempt_id, accepted_at, acceptance_sequence) VALUES (:event, :source, 'P02D-EVENT', :delivery, '1.0', 'DELIVERED', '2026-10-19T09:30:00Z', :input_event, :attempt_event, '2026-10-19T10:01:00Z', 1)",
        "INSERT INTO ilc.document_families VALUES (:family, :source, 'P02D-FAMILY', :delivery)",
        "INSERT INTO ilc.document_versions (document_key, family_key, source_system, delivery_key, document_id, version, schema_version, media_type, file_sha256, file_reference, file_size_bytes, input_key, accepted_attempt_id, accepted_at) VALUES (:document, :family, :source, :delivery, 'P02D-DOC', 1, '1.0', 'application/pdf', repeat('a',64), 'synthetic://p02d-sentinel.pdf', 100, :input_document, :attempt_document, '2026-10-19T10:01:00Z')",
        "INSERT INTO ilc.document_validities VALUES (:doc_validity, :family, :document, '2026-10-19T10:01:00Z', NULL)",
        "INSERT INTO ilc.extractions (extraction_key, document_key, input_key, attempt_id, extractor_version, outcome, extracted_at) VALUES (:extraction, :document, :input_document, :attempt_document, 'sentinel-v1', 'EXTRACTED', '2026-10-19T10:02:00Z')",
        "INSERT INTO ilc.evaluations (evaluation_key, document_key, input_key, delivery_key, attempt_id, extraction_key, completion_event_key, evaluation_number, result, rules_version, evaluated_at, expected_quantity, expected_quantity_unit) VALUES (:evaluation, :document, :input_document, :delivery, :attempt_document, :extraction, :event, 1, 'REVIEW_REQUIRED', 'sentinel-v1', '2026-10-19T10:03:00Z', 10, 'VOLUME')",
        "INSERT INTO ilc.evaluation_reasons VALUES (:reason, :evaluation, 'MISSING_REQUIRED_FIELD', 'receiver_name', 'Synthetic sentinel')",
        "INSERT INTO ilc.evaluation_validities VALUES (:eval_validity, :document, :evaluation, '2026-10-19T10:03:00Z', NULL)",
        "SET CONSTRAINTS ALL IMMEDIATE",
    ]
    for statement in statements:
        connection.execute(text(statement), params)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--expect-sha256")
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL TIME ZONE 'UTC'"))
            revision = connection.execute(text("SELECT version_num FROM public.alembic_version")).scalar_one()
            if revision not in {"0002_documents", "0003_decisions_conflicts"}:
                raise RuntimeError("Unexpected revision")
            if args.initialize:
                if revision != "0002_documents":
                    raise RuntimeError("Initialize before revision 0003")
                initialize(connection)
            if connection.execute(text("SELECT count(*) FROM ilc.document_versions WHERE source_system=:source"), {"source": SOURCE}).scalar_one() != 1:
                raise RuntimeError("Documentary sentinel missing")
            snapshot = {}
            for table in sorted(CORE_TABLES | DOCUMENT_TABLES):
                rows = connection.execute(text(f"SELECT row_to_json(t)::text FROM ilc.{table} t ORDER BY row_to_json(t)::text")).scalars().all()
                snapshot[table] = rows
            digest = hashlib.sha256(json.dumps(snapshot, ensure_ascii=True, sort_keys=True).encode("utf-8")).hexdigest()
            if args.expect_sha256 and digest != args.expect_sha256:
                raise RuntimeError("Previous table contents changed")
            print("Previous tables fingerprint SHA256:", digest)
            print("Documentary sentinel and 15-table snapshot: PASS (" + revision + ")")
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (SQLAlchemyError, OSError, ValueError, RuntimeError) as error:
        print(f"Preservation probe: FAIL ({type(error).__name__})")
        sys.exit(1)

"""Small handwritten structural fixtures; no parser or data generator."""

from tests.integration.test_core_migration import execute, insert_event, key, seed


def flush(connection):
    execute(connection, "SET CONSTRAINTS ALL IMMEDIATE")
    execute(connection, "SET CONSTRAINTS ALL DEFERRED")


def trace(connection, label, source="mock_a", kind="DOCUMENT"):
    input_key = key("doc-input:" + label)
    attempt_key = key("doc-attempt:" + label)
    execute(
        connection,
        """
        INSERT INTO ilc.inputs (input_key, source_system, input_type, original_reference,
            original_sha256, received_at, normalized_sha256, normalizer_version)
        VALUES (:input, :source, :kind, 'synthetic://document-probe', :hash,
            '2026-10-19T12:00:00Z', :hash, 'fixture-v1')
    """,
        input=input_key,
        source=source,
        kind=kind,
        hash="a" * 64,
    )
    execute(
        connection,
        """
        INSERT INTO ilc.receipts (receipt_key, input_key, attempt_received_at, original_reference, original_sha256)
        VALUES (:receipt, :input, '2026-10-19T12:00:00Z', 'synthetic://document-probe', :hash)
    """,
        receipt=key("doc-receipt:" + label),
        input=input_key,
        hash="a" * 64,
    )
    execute(
        connection,
        """
        INSERT INTO ilc.attempts (attempt_id, input_key, run_id, started_at, ended_at, outcome)
        VALUES (:attempt, :input, 'fixture', '2026-10-19T13:00:00Z', '2026-10-19T13:01:00Z', 'ACCEPTED')
    """,
        attempt=attempt_key,
        input=input_key,
    )
    return input_key, attempt_key


def family(connection, label, source="mock_a", external_id=None, delivery=None):
    execute(
        connection,
        """
        INSERT INTO ilc.document_families (family_key, source_system, document_family_id, delivery_key)
        VALUES (:family, :source, :external_id, :delivery)
    """,
        family=key("family:" + label),
        source=source,
        external_id=external_id or "POD-" + label,
        delivery=delivery or key("delivery"),
    )


def version(connection, label, **overrides):
    source = overrides.get("source", "mock_a")
    input_key, attempt_key = trace(
        connection,
        label,
        source=overrides.pop("input_source", source),
        kind=overrides.pop("input_type", "DOCUMENT"),
    )
    params = {
        "document": key("doc:" + label),
        "family": key("family:A"),
        "source": source,
        "delivery": key("delivery"),
        "external_id": "DOC-" + label,
        "version": 1,
        "previous": None,
        "hash": "a" * 64,
        "media": "application/pdf",
        "input": input_key,
        "attempt": attempt_key,
        "accepted": "2026-10-19T14:00:00Z",
        "size": 100,
    }
    params.update(overrides)
    execute(
        connection,
        """
        INSERT INTO ilc.document_versions (document_key, family_key, source_system, delivery_key,
            document_id, version, supersedes_document_key, schema_version, media_type,
            file_sha256, file_reference, file_size_bytes, input_key, accepted_attempt_id, accepted_at)
        VALUES (:document, :family, :source, :delivery, :external_id, :version, :previous,
            '1.0', :media, :hash, 'synthetic://document-probe.pdf', :size, :input, :attempt, :accepted)
    """,
        **params,
    )
    return params


def document_interval(
    connection,
    label,
    document,
    family_label="A",
    start="2026-10-19T14:00:00Z",
    end=None,
):
    execute(
        connection,
        """
        INSERT INTO ilc.document_validities (document_validity_key, family_key, document_key, valid_from, valid_to)
        VALUES (:id, :family, :document, :start, :end)
    """,
        id=key("document-validity:" + label),
        family=key("family:" + family_label),
        document=document,
        start=start,
        end=end,
    )


def extraction(connection, label, document_label="A1", **overrides):
    params = {
        "extraction": key("extraction:" + label),
        "document": key("doc:" + document_label),
        "input": key("doc-input:" + document_label),
        "attempt": key("doc-attempt:" + document_label),
        "outcome": "EXTRACTED",
        "error": None,
        "quantity": 10,
    }
    params.update(overrides)
    execute(
        connection,
        """
        INSERT INTO ilc.extractions (extraction_key, document_key, input_key, attempt_id,
            extractor_version, outcome, extracted_at, error_category, declared_delivery_id,
            delivered_at, received_quantity, quantity_unit, receiver_name)
        VALUES (:extraction, :document, :input, :attempt, 'fixture-extractor-v1', :outcome,
            '2026-10-19T15:00:00Z', :error, 'ENT-001', '2026-10-19T11:30:00Z', :quantity,
            'VOLUME', 'Synthetic receiver')
    """,
        **params,
    )


def evaluation(connection, label, document_label="A1", **overrides):
    params = {
        "evaluation": key("evaluation:" + label),
        "document": key("doc:" + document_label),
        "input": key("doc-input:" + document_label),
        "attempt": key("doc-attempt:" + document_label),
        "delivery": key("delivery"),
        "extraction": key("extraction:X1"),
        "event": key("event2"),
        "number": 1,
        "previous": None,
        "previous_number": None,
        "result": "REVIEW_REQUIRED",
        "manual": False,
        "author": None,
        "justification": None,
        "evaluated": "2026-10-19T15:10:00Z",
    }
    params.update(overrides)
    execute(
        connection,
        """
        INSERT INTO ilc.evaluations (evaluation_key, document_key, input_key, delivery_key,
            attempt_id, extraction_key, completion_event_key, evaluation_number,
            previous_evaluation_key, previous_evaluation_number, result, rules_version,
            evaluated_at, expected_quantity, expected_quantity_unit, expected_delivered_at,
            is_manual, author, justification)
        VALUES (:evaluation, :document, :input, :delivery, :attempt, :extraction, :event,
            :number, :previous, :previous_number, :result, 'fixture-rules-v1', :evaluated,
            10, 'VOLUME', '2026-10-19T11:30:00Z', :manual, :author, :justification)
    """,
        **params,
    )


def reason(
    connection,
    label,
    evaluation_label="E1",
    code="VALUE_MISMATCH",
    field="received_quantity",
):
    execute(
        connection,
        """
        INSERT INTO ilc.evaluation_reasons (reason_key, evaluation_key, code, affected_field)
        VALUES (:reason, :evaluation, :code, :field)
    """,
        reason=key("reason:" + label),
        evaluation=key("evaluation:" + evaluation_label),
        code=code,
        field=field,
    )


def evaluation_interval(
    connection,
    label,
    evaluation_label="E1",
    document_label="A1",
    start="2026-10-19T16:00:00Z",
    end=None,
):
    execute(
        connection,
        """
        INSERT INTO ilc.evaluation_validities (evaluation_validity_key, document_key, evaluation_key, valid_from, valid_to)
        VALUES (:id, :document, :evaluation, :start, :end)
    """,
        id=key("evaluation-validity:" + label),
        document=key("doc:" + document_label),
        evaluation=key("evaluation:" + evaluation_label),
        start=start,
        end=end,
    )


def seed_documents(connection):
    seed(connection)
    insert_event(connection, kind="DELIVERED", occurred="2026-10-19T11:30:00Z")
    family(connection, "A")
    family(connection, "B")
    family(connection, "C", source="mock_b", external_id="POD-A")
    a = version(connection, "A1")
    b = version(
        connection, "B1", family=key("family:B"), accepted="2026-10-19T14:01:00Z"
    )
    c = version(
        connection,
        "C1",
        family=key("family:C"),
        source="mock_b",
        external_id="DOC-A1",
        accepted="2026-10-19T14:02:00Z",
    )
    document_interval(connection, "A1", a["document"])
    document_interval(
        connection, "B1", b["document"], family_label="B", start=b["accepted"]
    )
    document_interval(
        connection, "C1", c["document"], family_label="C", start=c["accepted"]
    )
    extraction(connection, "X1", quantity=9)
    extraction(connection, "X2", document_label="B1")
    extraction(
        connection,
        "FAILED",
        outcome="PARSING_FAILED",
        error="PARSING_ERROR",
        quantity=None,
    )
    evaluation(connection, "E1")
    reason(connection, "R1")
    flush(connection)

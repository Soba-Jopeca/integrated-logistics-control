"""Structural positive/negative probes; no parsing or business-rule engine."""

import pytest
from sqlalchemy import inspect

from tests.integration.document_support import (
    document_interval,
    evaluation,
    evaluation_interval,
    execute,
    extraction,
    family,
    flush,
    key,
    reason,
    version,
)
from tests.integration.test_core_migration import expect_integrity


def rejects(connection, operation, state, constraint=None):
    def attempt():
        operation()
        flush(connection)

    expect_integrity(connection, attempt, state, constraint)


def replace_document(connection):
    execute(
        connection,
        "UPDATE ilc.document_validities SET valid_to = '2026-10-19T15:00:00Z' WHERE document_key = :doc",
        doc=key("doc:A1"),
    )
    next_version = version(
        connection,
        "A2",
        version=2,
        previous=key("doc:A1"),
        accepted="2026-10-19T15:00:00Z",
    )
    document_interval(
        connection, "A2", next_version["document"], start=next_version["accepted"]
    )
    flush(connection)


def test_catalog_and_author_composite_link(document_connection):
    catalog = inspect(document_connection)
    expected = {
        "sources",
        "inputs",
        "receipts",
        "runs",
        "attempts",
        "orders",
        "deliveries",
        "events",
        "document_families",
        "document_versions",
        "extractions",
        "evaluations",
        "evaluation_reasons",
        "document_validities",
        "evaluation_validities",
    }
    revision = execute(
        document_connection, "SELECT version_num FROM public.alembic_version"
    ).scalar_one()
    if revision == "0003_decisions_conflicts":
        expected |= {
            "completion_decisions",
            "conflicts",
            "conflict_evidence",
            "conflict_resolutions",
        }
    assert set(catalog.get_table_names(schema="ilc")) == expected
    links = {
        fk["name"]: fk for fk in catalog.get_foreign_keys("evaluations", schema="ilc")
    }
    link = links["fk_evaluations_extraction_document"]
    assert link["constrained_columns"] == ["extraction_key", "document_key"]
    assert link["referred_table"] == "extractions"
    assert link["referred_columns"] == ["extraction_key", "document_key"]
    extension = execute(
        document_connection,
        "SELECT extversion FROM pg_extension WHERE extname='btree_gist'",
    ).scalar_one()
    assert extension


def test_same_ids_in_other_source_and_distinct_families(document_connection):
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.document_families WHERE document_family_id='POD-A'",
        ).scalar_one()
        == 2
    )
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.document_versions WHERE document_id='DOC-A1'",
        ).scalar_one()
        == 2
    )
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.document_validities v JOIN ilc.document_families f USING (family_key) WHERE valid_to IS NULL AND f.source_system IN ('mock_a', 'mock_b')",
        ).scalar_one()
        == 3
    )


@pytest.mark.parametrize(
    ("changes", "state", "constraint"),
    [
        (
            {"version": 2, "previous": key("doc:B1")},
            "23503",
            "fk_documents_predecessor_family",
        ),
        (
            {"version": 3, "previous": key("doc:A1")},
            "23503",
            "fk_documents_predecessor_family",
        ),
        ({"version": 2, "previous": None}, "23514", "ck_documents_predecessor"),
        (
            {"version": 1, "previous": key("doc:B1")},
            "23514",
            "ck_documents_predecessor",
        ),
        ({"version": 0}, "23514", None),
        ({"source": "mock_b"}, "23503", "fk_documents_family_source_delivery"),
        ({"delivery": key("unknown")}, "23503", "fk_documents_family_source_delivery"),
        (
            {"input_source": "mock_b", "version": 2, "previous": key("doc:A1")},
            "23503",
            "fk_documents_input_source",
        ),
        (
            {"input_type": "EVENT", "version": 2, "previous": key("doc:A1")},
            "23503",
            "fk_documents_input_source",
        ),
        (
            {"attempt": key("attempt1"), "version": 2, "previous": key("doc:A1")},
            "23503",
            "fk_documents_attempt_input",
        ),
        (
            {"external_id": "DOC-A1", "version": 2, "previous": key("doc:A1")},
            "23505",
            "uq_documents_source_id",
        ),
        (
            {"external_id": "DOC-NEW", "version": 1, "previous": None},
            "23505",
            "uq_documents_family_version",
        ),
        ({"media": "image/png"}, "23514", "ck_documents_media"),
        ({"hash": "invalid"}, "23514", "ck_documents_hash"),
        ({"size": 0}, "23514", "ck_documents_size"),
    ],
)
def test_invalid_versions_preserve_current(
    document_connection, changes, state, constraint
):
    values = {"version": 2, "previous": key("doc:A1")}
    values.update(changes)
    rejects(
        document_connection,
        lambda: version(document_connection, "INVALID", **values),
        state,
        constraint,
    )
    assert execute(
        document_connection,
        "SELECT document_key::text FROM ilc.document_validities WHERE family_key=:family AND valid_to IS NULL",
        family=key("family:A"),
    ).scalar_one() == key("doc:A1")


def test_family_without_first_version_is_rejected(document_connection):
    rejects(
        document_connection,
        lambda: family(document_connection, "EMPTY"),
        "23514",
        "ck_family_chain_validity",
    )


def test_family_and_version_without_validity_are_rejected(document_connection):
    def operation():
        family(document_connection, "EMPTY")
        version(document_connection, "EMPTY1", family=key("family:EMPTY"))

    rejects(document_connection, operation, "23514", "ck_family_chain_validity")


def test_valid_replacement_keeps_previous_version_and_evaluation(document_connection):
    replace_document(document_connection)
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.document_versions WHERE family_key=:family",
            family=key("family:A"),
        ).scalar_one()
        == 2
    )
    assert execute(
        document_connection,
        "SELECT document_key::text FROM ilc.document_validities WHERE family_key=:family AND valid_to IS NULL",
        family=key("family:A"),
    ).scalar_one() == key("doc:A2")
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.evaluations WHERE document_key=:doc",
            doc=key("doc:A1"),
        ).scalar_one()
        == 1
    )
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.evaluations WHERE document_key=:doc",
            doc=key("doc:A2"),
        ).scalar_one()
        == 0
    )


def test_version_branch_is_rejected(document_connection):
    replace_document(document_connection)
    rejects(
        document_connection,
        lambda: version(
            document_connection, "BRANCH", version=2, previous=key("doc:A1")
        ),
        "23505",
    )


def test_document_open_validities_cannot_overlap(document_connection):
    def operation():
        second = version(
            document_connection,
            "A2",
            version=2,
            previous=key("doc:A1"),
            accepted="2026-10-19T15:00:00Z",
        )
        document_interval(
            document_connection, "A2", second["document"], start=second["accepted"]
        )

    rejects(document_connection, operation, "23P01", "ex_document_validity_overlap")


def test_closed_document_history_cannot_overlap(document_connection):
    replace_document(document_connection)

    def operation():
        third = version(
            document_connection,
            "A3",
            version=3,
            previous=key("doc:A2"),
            accepted="2026-10-19T16:00:00Z",
        )
        document_interval(
            document_connection,
            "BAD",
            third["document"],
            start="2026-10-19T14:30:00Z",
            end="2026-10-19T14:45:00Z",
        )

    rejects(document_connection, operation, "23P01", "ex_document_validity_overlap")


def test_validity_start_must_equal_acceptance(document_connection):
    def operation():
        family(document_connection, "NEW")
        doc = version(document_connection, "NEW1", family=key("family:NEW"))
        document_interval(
            document_connection,
            "NEW1",
            doc["document"],
            family_label="NEW",
            start="2026-10-19T15:00:00Z",
        )

    rejects(document_connection, operation, "23514", "ck_family_chain_validity")


def test_wrong_family_validity_is_rejected(document_connection):
    def operation():
        second = version(
            document_connection,
            "A2",
            version=2,
            previous=key("doc:A1"),
            accepted="2026-10-19T15:00:00Z",
        )
        document_interval(
            document_connection,
            "WRONG",
            second["document"],
            family_label="B",
            start="2026-10-19T13:00:00Z",
            end="2026-10-19T13:30:00Z",
        )

    rejects(document_connection, operation, "23503", "fk_document_validity_family")


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE ilc.document_families SET document_family_id='CHANGED'",
        "DELETE FROM ilc.document_families",
        "UPDATE ilc.document_versions SET file_sha256=repeat('b',64)",
        "DELETE FROM ilc.document_versions",
        "UPDATE ilc.extractions SET received_quantity=99",
        "DELETE FROM ilc.extractions",
        "UPDATE ilc.evaluations SET expected_quantity=99",
        "DELETE FROM ilc.evaluations",
        "UPDATE ilc.evaluation_reasons SET code='PARSING_ERROR'",
        "DELETE FROM ilc.evaluation_reasons",
        "DELETE FROM ilc.document_validities",
    ],
)
def test_documentary_history_cannot_be_overwritten_or_deleted(document_connection, sql):
    rejects(document_connection, lambda: execute(document_connection, sql), "23514")


def test_closed_document_interval_cannot_be_reopened(document_connection):
    replace_document(document_connection)
    rejects(
        document_connection,
        lambda: execute(
            document_connection,
            "UPDATE ilc.document_validities SET valid_to=NULL WHERE document_key=:doc",
            doc=key("doc:A1"),
        ),
        "23514",
    )


def test_extraction_and_evaluation_must_share_version(document_connection):
    rejects(
        document_connection,
        lambda: evaluation(
            document_connection, "WRONG", number=2, extraction=key("extraction:X2")
        ),
        "23503",
        "fk_evaluations_extraction_document",
    )


def test_extraction_attempt_must_belong_to_document_input(document_connection):
    rejects(
        document_connection,
        lambda: extraction(document_connection, "WRONG", attempt=key("doc-attempt:B1")),
        "23503",
        "fk_extractions_attempt_input",
    )


def test_extraction_may_preserve_missing_and_invalid_values(document_connection):
    extraction(document_connection, "MISSING", quantity=None)
    extraction(document_connection, "NEGATIVE", quantity=-1)
    flush(document_connection)
    quantities = (
        execute(
            document_connection,
            "SELECT received_quantity FROM ilc.extractions WHERE extraction_key IN (:a,:b)",
            a=key("extraction:MISSING"),
            b=key("extraction:NEGATIVE"),
        )
        .scalars()
        .all()
    )
    assert None in quantities and -1 in quantities


def test_structurally_supported_approval_has_no_reasons(document_connection):
    evaluation(
        document_connection,
        "APPROVED",
        document_label="B1",
        extraction=key("extraction:X2"),
        result="APPROVED",
    )
    flush(document_connection)


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        (
            {"result": "APPROVED", "extraction": None},
            "ck_evaluation_successful_extraction",
        ),
        ({"result": "APPROVED", "event": None}, "ck_evaluations_prerequisites"),
        (
            {"result": "APPROVED", "extraction": key("extraction:FAILED")},
            "ck_evaluation_successful_extraction",
        ),
        ({"result": "NOT_EVALUATED"}, "ck_evaluations_result"),
        ({"manual": True}, "ck_evaluations_manual"),
        (
            {"previous": key("evaluation:E1"), "previous_number": 2},
            "ck_evaluations_previous",
        ),
        ({"previous": key("evaluation:E1")}, "ck_evaluations_previous"),
    ],
)
def test_invalid_evaluation_structure(document_connection, changes, constraint):
    rejects(
        document_connection,
        lambda: evaluation(document_connection, "INVALID", number=2, **changes),
        "23514",
        constraint,
    )


def test_previous_evaluation_must_belong_to_same_document(document_connection):
    evaluation(
        document_connection,
        "OTHER",
        document_label="B1",
        extraction=key("extraction:X2"),
        result="APPROVED",
    )
    flush(document_connection)
    rejects(
        document_connection,
        lambda: evaluation(
            document_connection,
            "WRONG",
            number=2,
            previous=key("evaluation:OTHER"),
            previous_number=1,
        ),
        "23503",
        "fk_evaluations_previous_document",
    )


def test_manual_revision_preserves_previous_evaluation(document_connection):
    evaluation(
        document_connection,
        "MANUAL",
        number=2,
        previous=key("evaluation:E1"),
        previous_number=1,
        manual=True,
        author="Synthetic reviewer",
        justification="Synthetic structural review",
    )
    reason(document_connection, "MANUAL", evaluation_label="MANUAL")
    flush(document_connection)
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.evaluations WHERE document_key=:doc",
            doc=key("doc:A1"),
        ).scalar_one()
        == 2
    )


def test_review_requires_a_reason_at_transaction_end(document_connection):
    rejects(
        document_connection,
        lambda: evaluation(document_connection, "EMPTY", number=2, extraction=None),
        "23514",
        "ck_evaluation_reason_set",
    )


def test_approved_evaluation_cannot_have_blocker_reason(document_connection):
    def operation():
        evaluation(
            document_connection,
            "APPROVED",
            document_label="B1",
            extraction=key("extraction:X2"),
            result="APPROVED",
        )
        reason(document_connection, "BAD", evaluation_label="APPROVED")

    rejects(document_connection, operation, "23514", "ck_evaluation_reason_set")


def test_reason_uniqueness_includes_null_field(document_connection):
    def operation():
        reason(document_connection, "NULL1", code="MISSING_REQUIRED_FIELD", field=None)
        reason(document_connection, "NULL2", code="MISSING_REQUIRED_FIELD", field=None)

    rejects(document_connection, operation, "23505", "uq_reasons_code_field")


def test_selected_evaluation_must_belong_to_document(document_connection):
    rejects(
        document_connection,
        lambda: evaluation_interval(document_connection, "WRONG", document_label="B1"),
        "23503",
        "fk_evaluation_validity_document",
    )


def test_evaluation_cannot_be_selected_before_production(document_connection):
    rejects(
        document_connection,
        lambda: evaluation_interval(
            document_connection, "EARLY", start="2026-10-19T15:00:00Z"
        ),
        "23514",
        "ck_evaluation_validity_production",
    )


@pytest.mark.parametrize(
    ("first_end", "second_start", "second_end"),
    [
        (None, "2026-10-19T17:00:00Z", None),
        ("2026-10-19T17:00:00Z", "2026-10-19T16:30:00Z", "2026-10-19T18:00:00Z"),
    ],
)
def test_evaluation_validities_cannot_overlap(
    document_connection, first_end, second_start, second_end
):
    evaluation_interval(document_connection, "FIRST", end=first_end)
    flush(document_connection)
    rejects(
        document_connection,
        lambda: evaluation_interval(
            document_connection, "SECOND", start=second_start, end=second_end
        ),
        "23P01",
        "ex_evaluation_validity_overlap",
    )


def test_adjacent_evaluation_intervals_are_valid(document_connection):
    evaluation_interval(document_connection, "FIRST", end="2026-10-19T17:00:00Z")
    evaluation_interval(document_connection, "SECOND", start="2026-10-19T17:00:00Z")
    flush(document_connection)
    assert (
        execute(
            document_connection,
            "SELECT count(*) FROM ilc.evaluation_validities WHERE document_key IN (SELECT document_key FROM ilc.document_versions WHERE source_system IN ('mock_a', 'mock_b'))",
        ).scalar_one()
        == 2
    )


def test_empty_evaluation_interval_is_rejected(document_connection):
    rejects(
        document_connection,
        lambda: evaluation_interval(
            document_connection, "EMPTY", end="2026-10-19T16:00:00Z"
        ),
        "23514",
        "ck_evaluation_validity_interval",
    )


def test_evaluation_interval_can_close_once_only(document_connection):
    evaluation_interval(document_connection, "FIRST")
    execute(
        document_connection,
        "UPDATE ilc.evaluation_validities SET valid_to='2026-10-19T17:00:00Z'",
    )
    flush(document_connection)
    rejects(
        document_connection,
        lambda: execute(
            document_connection, "UPDATE ilc.evaluation_validities SET valid_to=NULL"
        ),
        "23514",
    )
    rejects(
        document_connection,
        lambda: execute(document_connection, "DELETE FROM ilc.evaluation_validities"),
        "23514",
    )


def test_expected_values_in_historical_evaluation_are_preserved(document_connection):
    execute(document_connection, "UPDATE ilc.deliveries SET expected_quantity=20")
    assert (
        execute(
            document_connection,
            "SELECT expected_quantity FROM ilc.evaluations WHERE evaluation_key=:id",
            id=key("evaluation:E1"),
        ).scalar_one()
        == 10
    )

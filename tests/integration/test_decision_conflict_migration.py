"""Handwritten structural probes; no operational conflict resolution engine."""

import pytest
from sqlalchemy import inspect

from tests.integration.document_support import execute, flush, key
from tests.integration.test_core_migration import insert_event
from tests.integration.test_document_migration import rejects


def completion(connection, label="D1", **changes):
    params = {
        "id": key("decision:" + label), "delivery": key("delivery"),
        "event": key("event2"), "event_type": "DELIVERED", "number": 1,
        "previous": None, "previous_time": None, "time": "2026-10-19T17:00:00Z",
        "kind": "PROVISIONAL", "author": "synthetic-system", "reason": "Synthetic choice",
    }
    params.update(changes)
    execute(connection, """
        INSERT INTO ilc.completion_decisions (completion_decision_key, delivery_key,
            event_key, event_type, decision_number, previous_decision_key,
            previous_decided_at, decided_at, decision_type, author, reason)
        VALUES (:id, :delivery, :event, :event_type, :number, :previous,
            :previous_time, :time, :kind, :author, :reason)
    """, **params)


def conflict(connection, label="C1", **changes):
    params = {"id": key("conflict:" + label), "delivery": key("delivery"),
              "kind": "COMPLETION_CONFLICT", "time": "2026-10-19T16:00:00Z",
              "reason": "Synthetic alternative"}
    params.update(changes)
    execute(connection, """
        INSERT INTO ilc.conflicts (conflict_key, delivery_key, conflict_type, opened_at, reason)
        VALUES (:id, :delivery, :kind, :time, :reason)
    """, **params)


def evidence(connection, label, **changes):
    params = {"id": key("evidence:" + label), "conflict": key("conflict:C1"),
              "input": key("input2"), "event": key("event2"), "document": None,
              "role": "ORIGINAL", "time": "2026-10-19T16:10:00Z"}
    params.update(changes)
    execute(connection, """
        INSERT INTO ilc.conflict_evidence (conflict_evidence_key, conflict_key, input_key,
            event_key, document_key, evidence_role, recorded_at)
        VALUES (:id, :conflict, :input, :event, :document, :role, :time)
    """, **params)


def pair(connection, label="C1", **changes):
    conflict(connection, label, **changes)
    evidence(connection, label + "original", conflict=key("conflict:" + label))
    evidence(connection, label + "alternative", conflict=key("conflict:" + label),
             input=key("input3"), event=key("event3"), role="ALTERNATIVE")


def resolution(connection, label="R1", **changes):
    params = {"id": key("resolution:" + label), "conflict": key("conflict:C1"),
              "delivery": key("delivery"), "completion": key("decision:D1"),
              "number": 1, "previous": None, "previous_time": None,
              "time": "2026-10-19T18:00:00Z", "author": "Synthetic reviewer",
              "reason": "Synthetic explicit choice", "decision": "SELECT_COMPLETION"}
    params.update(changes)
    execute(connection, """
        INSERT INTO ilc.conflict_resolutions (resolution_key, conflict_key, delivery_key,
            completion_decision_key, resolution_number, previous_resolution_key,
            previous_resolved_at, resolved_at, author, reason, decision)
        VALUES (:id, :conflict, :delivery, :completion, :number, :previous,
            :previous_time, :time, :author, :reason, :decision)
    """, **params)


@pytest.fixture
def decision_connection(document_connection):
    revision = execute(document_connection, "SELECT version_num FROM public.alembic_version").scalar_one()
    assert revision == "0003_decisions_conflicts"
    insert_event(document_connection, event_key=key("event3"), number=3,
                 source="mock_b", event_id="EVT-003", kind="DELIVERED",
                 sequence=3, occurred="2026-10-19T11:40:00Z")
    execute(document_connection, """
        INSERT INTO ilc.orders VALUES (:order, 'mock_a', 'ORDER-OTHER', '2026-10-19T10:00:00Z', '{}')
    """, order=key("other-order"))
    execute(document_connection, """
        INSERT INTO ilc.deliveries VALUES (:delivery, :order, 'ENT-OTHER', NULL, 10, 'VOLUME')
    """, delivery=key("other-delivery"), order=key("other-order"))
    return document_connection


def test_catalog_and_joao_link(decision_connection):
    catalog = inspect(decision_connection)
    assert len(catalog.get_table_names(schema="ilc")) == 19
    links = {fk["name"]: fk for fk in catalog.get_foreign_keys("completion_decisions", schema="ilc")}
    link = links["fk_completion_event_delivery"]
    assert link["constrained_columns"] == ["event_key", "delivery_key", "event_type"]
    assert link["referred_table"] == "events"
    assert link["referred_columns"] == ["event_key", "delivery_key", "event_type"]


def test_valid_manual_chain_and_alternatives(decision_connection):
    c = decision_connection
    completion(c)
    completion(c, "D2", event=key("event3"), number=2,
               previous=key("decision:D1"), previous_time="2026-10-19T17:00:00Z",
               time="2026-10-19T17:30:00Z", kind="MANUAL", author="Synthetic reviewer")
    pair(c)
    resolution(c, completion=key("decision:D2"))
    resolution(c, "R2", number=2, previous=key("resolution:R1"),
               previous_time="2026-10-19T18:00:00Z", time="2026-10-19T19:00:00Z")
    flush(c)
    assert execute(c, "SELECT count(*) FROM ilc.completion_decisions").scalar_one() == 2
    assert execute(c, "SELECT count(*) FROM ilc.conflict_evidence").scalar_one() == 2
    assert execute(c, "SELECT count(*) FROM ilc.conflict_resolutions").scalar_one() == 2
    assert execute(c, "SELECT count(*) FROM ilc.events WHERE source_system IN ('mock_a', 'mock_b')").scalar_one() == 3


def test_unresolved_delivery_and_later_audited_link(decision_connection):
    c = decision_connection
    pair(c, delivery=None)
    flush(c)
    assert execute(c, "SELECT delivery_key IS NULL FROM ilc.conflicts").scalar_one()
    completion(c)
    resolution(c)
    flush(c)
    assert execute(c, "SELECT delivery_key IS NULL FROM ilc.conflicts").scalar_one()
    assert execute(c, "SELECT delivery_key FROM ilc.conflict_resolutions").scalar_one() is not None


@pytest.mark.parametrize(("changes", "state", "constraint"), [
    ({"event": key("event1")}, "23503", "fk_completion_event_delivery"),
    ({"delivery": key("other-delivery")}, "23503", "fk_completion_event_delivery"),
    ({"event": key("missing")}, "23503", "fk_completion_event_delivery"),
    ({"event_type": "IN_TRANSIT"}, "23514", "ck_completion_event_type"),
    ({"author": " "}, "23514", "ck_completion_author"),
    ({"reason": " "}, "23514", "ck_completion_reason"),
    ({"kind": "AUTOMATIC_RESOLUTION"}, "23514", "ck_completion_type"),
    ({"number": 0}, "23514", "ck_completion_number"),
    ({"time": "infinity"}, "23514", "ck_completion_time"),
    ({"previous": key("decision:D1")}, "23514", "ck_completion_previous"),
])
def test_invalid_completion(decision_connection, changes, state, constraint):
    rejects(decision_connection, lambda: completion(decision_connection, **changes), state, constraint)


@pytest.mark.parametrize(("changes", "state", "constraint"), [
    ({"number": 3}, "23503", "fk_completion_previous"),
    ({"previous": key("missing")}, "23503", "fk_completion_previous"),
    ({"previous": key("decision:D2")}, "23503", "fk_completion_previous"),
    ({"previous_time": "2026-10-19T16:59:00Z"}, "23503", "fk_completion_previous"),
    ({"time": "2026-10-19T16:00:00Z"}, "23514", "ck_completion_previous"),
])
def test_completion_chain_rejects_gaps_cycles_and_time(decision_connection, changes, state, constraint):
    c = decision_connection
    completion(c)
    params = {"number": 2, "previous": key("decision:D1"),
              "previous_time": "2026-10-19T17:00:00Z", "time": "2026-10-19T17:30:00Z"}
    params.update(changes)
    rejects(c, lambda: completion(c, "D2", **params), state, constraint)


def test_completion_previous_cannot_cross_delivery(decision_connection):
    c = decision_connection
    completion(c)
    rejects(c, lambda: completion(c, "D2", delivery=key("other-delivery"),
            number=2, previous=key("decision:D1"), previous_time="2026-10-19T17:00:00Z"),
            "23503")


def test_completion_cannot_branch(decision_connection):
    c = decision_connection
    completion(c)
    params = {"number": 2, "previous": key("decision:D1"), "previous_time": "2026-10-19T17:00:00Z"}
    completion(c, "D2", **params)
    rejects(c, lambda: completion(c, "D3", **params), "23505")


@pytest.mark.parametrize(("changes", "constraint"), [
    ({"author": " "}, "ck_resolution_author"),
    ({"reason": " "}, "ck_resolution_reason"),
    ({"decision": " "}, "ck_resolution_decision"),
    ({"time": "2026-10-19T15:00:00Z"}, "ck_resolution_chronology"),
    ({"time": "2026-10-19T16:05:00Z"}, "ck_resolution_chronology"),
    ({"delivery": key("other-delivery")}, "ck_resolution_delivery"),
    ({"delivery": None}, "ck_resolution_delivery"),
])
def test_invalid_resolution(decision_connection, changes, constraint):
    c = decision_connection
    completion(c)
    pair(c)
    rejects(c, lambda: resolution(c, **changes), "23514", constraint)


@pytest.mark.parametrize(("changes", "state", "constraint"), [
    ({"number": 3}, "23503", "fk_resolution_previous"),
    ({"previous": key("resolution:R2")}, "23503", "fk_resolution_previous"),
    ({"previous": key("missing")}, "23503", "fk_resolution_previous"),
    ({"previous_time": "2026-10-19T17:59:00Z"}, "23503", "fk_resolution_previous"),
    ({"time": "2026-10-19T17:30:00Z"}, "23514", "ck_resolution_previous"),
])
def test_resolution_chain(decision_connection, changes, state, constraint):
    c = decision_connection
    completion(c)
    pair(c)
    resolution(c)
    params = {"number": 2, "previous": key("resolution:R1"),
              "previous_time": "2026-10-19T18:00:00Z", "time": "2026-10-19T19:00:00Z"}
    params.update(changes)
    rejects(c, lambda: resolution(c, "R2", **params), state, constraint)


def test_resolution_previous_cannot_cross_conflict(decision_connection):
    c = decision_connection
    completion(c)
    pair(c)
    pair(c, "C2")
    resolution(c)
    rejects(c, lambda: resolution(c, "R2", conflict=key("conflict:C2"), number=2,
            previous=key("resolution:R1"), previous_time="2026-10-19T18:00:00Z"),
            "23503", "fk_resolution_previous")


def test_resolution_cannot_branch(decision_connection):
    c = decision_connection
    completion(c)
    pair(c)
    resolution(c)
    params = {"number": 2, "previous": key("resolution:R1"), "previous_time": "2026-10-19T18:00:00Z"}
    resolution(c, "R2", **params)
    rejects(c, lambda: resolution(c, "R3", **params), "23505")


@pytest.mark.parametrize(("changes", "state", "constraint"), [
    ({"input": key("input1")}, "23503", "fk_evidence_event_input"),
    ({"event": None, "document": key("doc:A1")}, "23503", "fk_evidence_document_input"),
    ({"document": key("doc:A1")}, "23514", "ck_evidence_single_object"),
    ({"role": "UNKNOWN"}, "23514", "ck_evidence_role"),
    ({"time": "2026-10-19T15:00:00Z"}, "23514", "ck_evidence_chronology"),
])
def test_invalid_evidence(decision_connection, changes, state, constraint):
    c = decision_connection
    conflict(c)
    rejects(c, lambda: evidence(c, "invalid", **changes), state, constraint)


def test_conflict_requires_distinct_original_and_alternative(decision_connection):
    c = decision_connection
    rejects(c, lambda: conflict(c), "23514", "ck_conflict_evidence_set")
    def only_original():
        conflict(c)
        evidence(c, "original")
    rejects(c, only_original, "23514", "ck_conflict_evidence_set")
    conflict(c)
    evidence(c, "original")
    rejects(c, lambda: evidence(c, "duplicate", role="ALTERNATIVE"), "23505", "uq_conflict_evidence_input")


def test_unaccepted_input_is_preserved_as_alternative(decision_connection):
    c = decision_connection
    conflict(c)
    evidence(c, "original")
    evidence(c, "alternative", event=None, input=key("input1"), role="ALTERNATIVE")
    flush(c)
    assert execute(c, "SELECT count(*) FROM ilc.events WHERE source_system IN ('mock_a', 'mock_b')").scalar_one() == 3


def test_document_evidence_uses_its_own_input(decision_connection):
    c = decision_connection
    conflict(c)
    evidence(c, "original", event=None, document=key("doc:A1"), input=key("doc-input:A1"))
    evidence(c, "alternative", event=None, document=key("doc:B1"), input=key("doc-input:B1"), role="ALTERNATIVE")
    flush(c)


def test_known_conflict_rejects_evidence_of_other_delivery(decision_connection):
    c = decision_connection
    conflict(c, delivery=key("other-delivery"))
    rejects(c, lambda: evidence(c, "wrong"), "23514", "ck_evidence_delivery")


def test_late_binding_rejects_delivery_different_from_evidence(decision_connection):
    c = decision_connection
    pair(c, delivery=None)
    rejects(c, lambda: resolution(c, delivery=key("other-delivery"), completion=None), "23514", "ck_resolution_delivery")


def test_evidence_sealed_after_resolution(decision_connection):
    c = decision_connection
    completion(c)
    pair(c)
    resolution(c)
    rejects(c, lambda: evidence(c, "late", input=key("input1"), event=None), "23514", "ck_evidence_sealed")


def test_resolution_cannot_select_unknown_decision(decision_connection):
    c = decision_connection
    pair(c)
    rejects(c, lambda: resolution(c), "23503", "fk_resolution_completion_delivery")


def test_unbound_conflict_can_have_resolution_without_invented_delivery(decision_connection):
    c = decision_connection
    pair(c, delivery=None)
    resolution(c, delivery=None, completion=None, decision="KEEP_UNRESOLVED_REFERENCE")
    flush(c)


def test_later_resolution_cannot_erase_audited_delivery(decision_connection):
    c = decision_connection
    pair(c, delivery=None)
    resolution(c, completion=None)
    rejects(c, lambda: resolution(c, "R2", delivery=None, completion=None,
            number=2, previous=key("resolution:R1"), previous_time="2026-10-19T18:00:00Z"),
            "23514", "ck_resolution_delivery")


@pytest.mark.parametrize("table", ["completion_decisions", "conflicts", "conflict_evidence", "conflict_resolutions"])
@pytest.mark.parametrize("action", ["UPDATE", "DELETE"])
def test_immutable_history(decision_connection, table, action):
    c = decision_connection
    completion(c)
    pair(c)
    resolution(c)
    sql = f"DELETE FROM ilc.{table}" if action == "DELETE" else f"UPDATE ilc.{table} SET " + {
        "completion_decisions": "reason='changed'", "conflicts": "reason='changed'",
        "conflict_evidence": "evidence_role='ALTERNATIVE'", "conflict_resolutions": "reason='changed'",
    }[table]
    rejects(c, lambda: execute(c, sql), "23514")

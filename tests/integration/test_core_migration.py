"""Transactional synthetic probes against the explicitly enabled disposable DB."""

import os
from uuid import NAMESPACE_URL, uuid5

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from scripts.migration_config import TEST_DATABASE, test_engine as make_engine


def key(name):
    return str(uuid5(NAMESPACE_URL, "ilc-f2p02b/" + name))


def execute(connection, sql, **params):
    return connection.execute(text(sql), params)


@pytest.fixture
def connection():
    if os.environ.get("ILC_TEST_DATABASE") != TEST_DATABASE:
        pytest.fail("Set ILC_TEST_DATABASE=ilc_f2p02b_test explicitly")
    engine = make_engine(TEST_DATABASE)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                revision = execute(connection, "SELECT version_num FROM public.alembic_version").scalar_one()
                if revision != "0001_core":
                    pytest.fail("Upgrade to 0001_core before running these probes")
                seed(connection)
                yield connection
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def seed(connection):
    execute(connection, "INSERT INTO ilc.sources VALUES ('mock_a', 'Synthetic A'), ('mock_b', 'Synthetic B')")
    execute(connection, """
        INSERT INTO ilc.runs (run_id, stage, started_at, ended_at, status)
        VALUES ('fixture', 'constraint_probe', '2026-10-19T12:00:00Z', '2026-10-19T12:01:00Z', 'SUCCEEDED')
    """)
    for number, source, kind in [(1, "mock_a", "EVENT"), (2, "mock_a", "EVENT"), (3, "mock_b", "EVENT"), (4, "mock_a", "DOCUMENT")]:
        execute(connection, """
            INSERT INTO ilc.inputs (input_key, source_system, input_type, original_reference,
                original_sha256, received_at, normalized_sha256, normalizer_version)
            VALUES (:input, :source, :kind, 'synthetic://probe', :hash,
                '2026-10-19T12:00:00Z', :hash, 'fixture-v1')
        """, input=key(f"input{number}"), source=source, kind=kind, hash="a" * 64)
        execute(connection, """
            INSERT INTO ilc.receipts (receipt_key, input_key, attempt_received_at, original_reference, original_sha256)
            VALUES (:receipt, :input, '2026-10-19T12:00:00Z', 'synthetic://probe', :hash)
        """, receipt=key(f"receipt{number}"), input=key(f"input{number}"), hash="a" * 64)
        execute(connection, """
            INSERT INTO ilc.attempts (attempt_id, input_key, run_id, receipt_key, started_at, ended_at, outcome)
            VALUES (:attempt, :input, 'fixture', :receipt, '2026-10-19T12:00:00Z', '2026-10-19T12:01:00Z', 'ACCEPTED')
        """, attempt=key(f"attempt{number}"), input=key(f"input{number}"), receipt=key(f"receipt{number}"))
    execute(connection, """
        INSERT INTO ilc.orders (order_key, source_system, order_id, released_at, request_data)
        VALUES (:order, 'mock_a', 'ORDER-001', '2026-10-19T10:00:00Z', '{}')
    """, order=key("order"))
    execute(connection, """
        INSERT INTO ilc.deliveries (delivery_key, order_key, delivery_id, expected_quantity, quantity_unit)
        VALUES (:delivery, :order, 'ENT-001', 10, 'VOLUME')
    """, delivery=key("delivery"), order=key("order"))
    insert_event(connection, event_key=key("event1"), number=1, event_id="EVT-001", sequence=1)


def insert_event(connection, **overrides):
    params = {
        "event_key": key("event2"), "source": "mock_a", "event_id": "EVT-002",
        "delivery": key("delivery"), "schema": "1.0", "kind": "IN_TRANSIT",
        "occurred": "2026-10-19T11:00:00Z", "input": key("input2"),
        "attempt": key("attempt2"), "sequence": 2,
    }
    number = overrides.pop("number", None)
    if number is not None:
        params.update(input=key(f"input{number}"), attempt=key(f"attempt{number}"))
    params.update(overrides)
    return execute(connection, """
        INSERT INTO ilc.events (event_key, source_system, event_id, delivery_key, schema_version,
            event_type, occurred_at, input_key, accepted_attempt_id, accepted_at, acceptance_sequence)
        VALUES (:event_key, :source, :event_id, :delivery, :schema, :kind,
            :occurred, :input, :attempt, '2026-10-19T12:01:00Z', :sequence)
    """, **params)


def expect_integrity(connection, operation, state, constraint=None):
    with pytest.raises(IntegrityError) as caught:
        with connection.begin_nested():
            operation()
    assert caught.value.orig.sqlstate == state
    if constraint:
        assert caught.value.orig.diag.constraint_name == constraint


def test_physical_slice_and_author_constraint(connection):
    catalog = inspect(connection)
    assert set(catalog.get_table_names(schema="ilc")) == {
        "sources", "inputs", "receipts", "runs", "attempts", "orders", "deliveries", "events",
    }
    constraints = {c["name"]: c["column_names"] for c in catalog.get_unique_constraints("events", schema="ilc")}
    assert constraints["uq_events_source_event"] == ["source_system", "event_id"]


def test_valid_event_with_earlier_occurrence(connection):
    insert_event(connection, occurred="2026-10-19T10:30:00Z")
    assert execute(connection, "SELECT count(*) FROM ilc.events").scalar_one() == 2


def test_same_event_id_in_another_source_is_valid(connection):
    insert_event(connection, number=3, source="mock_b", event_id="EVT-001")
    assert execute(connection, "SELECT count(*) FROM ilc.events").scalar_one() == 2


@pytest.mark.parametrize(("overrides", "state", "constraint"), [
    ({"event_id": "EVT-001"}, "23505", "uq_events_source_event"),
    ({"sequence": 1}, "23505", "uq_events_sequence"),
    ({"delivery": key("unknown")}, "23503", "events_delivery_key_fkey"),
    ({"attempt": key("attempt1")}, "23503", "fk_events_attempt_input"),
    ({"source": "mock_b"}, "23503", "fk_events_input_source"),
    ({"number": 4}, "23503", "fk_events_input_source"),
    ({"event_id": None}, "23502", None),
    ({"event_id": " EVT-002"}, "23514", "ck_events_id"),
    ({"kind": "FINISHED"}, "23514", "ck_events_type"),
    ({"schema": "2.0"}, "23514", "ck_events_schema"),
    ({"sequence": 0}, "23514", "ck_events_sequence"),
])
def test_invalid_events_leave_original_unchanged(connection, overrides, state, constraint):
    expect_integrity(connection, lambda: insert_event(connection, **overrides), state, constraint)
    assert execute(connection, "SELECT count(*) FROM ilc.events").scalar_one() == 1


@pytest.mark.parametrize(("sql", "state", "constraint"), [
    ("INSERT INTO ilc.deliveries VALUES (:new, :order, 'ENT-002', NULL, 10, 'VOLUME')", "23505", "uq_deliveries_order"),
    ("UPDATE ilc.deliveries SET expected_quantity = -1", "23514", "ck_deliveries_quantity"),
    ("UPDATE ilc.deliveries SET quantity_unit = ''", "23514", "ck_deliveries_unit"),
    ("DELETE FROM ilc.orders WHERE order_key = :order", "23503", "deliveries_order_key_fkey"),
    ("UPDATE ilc.inputs SET original_sha256 = repeat('b', 64)", "23514", None),
    ("DELETE FROM ilc.receipts", "23514", None),
    ("UPDATE ilc.events SET occurred_at = '2026-10-19T13:00:00Z'", "23514", None),
    ("DELETE FROM ilc.events", "23514", None),
    ("UPDATE ilc.runs SET ended_at = '2026-10-19T11:00:00Z'", "23514", "ck_runs_time"),
    ("UPDATE ilc.attempts SET outcome = NULL", "23514", "ck_attempts_state"),
    ("UPDATE ilc.attempts SET receipt_key = :other_receipt WHERE attempt_id = :attempt", "23503", "fk_attempts_receipt_input"),
])
def test_domain_and_traceability_restrictions(connection, sql, state, constraint):
    params = dict(new=key("other"), order=key("order"), other_receipt=key("receipt2"), attempt=key("attempt1"))
    expect_integrity(connection, lambda: execute(connection, sql, **params), state, constraint)


def test_internal_retry_preserves_first_receipt(connection):
    execute(connection, """
        INSERT INTO ilc.attempts (attempt_id, input_key, run_id, started_at)
        VALUES (:attempt, :input, 'fixture', '2026-10-19T13:00:00Z')
    """, attempt=key("retry"), input=key("input1"))
    assert execute(connection, "SELECT count(*) FROM ilc.receipts").scalar_one() == 4
    assert execute(connection, "SELECT receipt_key IS NULL FROM ilc.attempts WHERE attempt_id = :id", id=key("retry")).scalar_one()


def test_database_user_has_no_administrative_privileges(connection):
    flags = execute(connection, """
        SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
        FROM pg_roles WHERE rolname = current_user
    """).one()
    assert not any(flags)


@pytest.mark.parametrize(("hash_value", "normalizer", "state", "constraint"), [
    ("INVALID", "fixture-v1", "23514", "ck_inputs_hash"),
    ("A" * 64, "fixture-v1", "23514", "ck_inputs_hash"),
    ("b" * 64, None, "23514", "ck_inputs_normalization"),
])
def test_input_checksums_and_normalization_pair(connection, hash_value, normalizer, state, constraint):
    sql = """
        INSERT INTO ilc.inputs (input_key, source_system, input_type, original_reference,
            original_sha256, received_at, normalized_sha256, normalizer_version)
        VALUES (:input, 'mock_a', 'EVENT', 'synthetic://invalid', :hash,
            '2026-10-19T12:00:00Z', :normalized, :normalizer)
    """
    expect_integrity(connection, lambda: execute(connection, sql,
        input=key("invalid_input"), hash=hash_value,
        normalized="b" * 64, normalizer=normalizer), state, constraint)

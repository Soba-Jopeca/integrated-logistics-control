"""HTTP real + banco explicitamente selecionado; evidencias preservadas por run_id."""

import hashlib
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from scripts.api_capture import capture, now, write_page
from scripts.check_api_failures import local_server
from scripts.migration_config import TEST_DATABASE
from scripts.migration_config import test_engine as make_engine


@pytest.fixture
def engine():
    if os.environ.get("ILC_CAPTURE_TEST_DATABASE") != TEST_DATABASE:
        pytest.skip("Set ILC_CAPTURE_TEST_DATABASE=ilc_f2p02b_test explicitly")
    selected = make_engine(TEST_DATABASE)
    try:
        yield selected
    finally:
        selected.dispose()


def recover(connection, run_id):
    pages = connection.execute(
        text("""
        SELECT response_body,response_sha256,item_count,capture_status
        FROM ilc.capture_pages WHERE run_id=:run ORDER BY page_number
    """),
        {"run": run_id},
    ).all()
    events = []
    for body, checksum, count, status in pages:
        raw = bytes(body)
        assert hashlib.sha256(raw).hexdigest() == checksum
        data = json.loads(raw)
        if status == "CAPTURED":
            assert len(data["items"]) == count
            events.extend(data["items"])
    return pages, events


def test_real_http_capture_13_and_partial_failure(engine):
    from mock_api.app import FIXTURE

    records = [json.loads(line) for line in FIXTURE.read_text().splitlines() if line]
    expected = [
        record
        for _, record in sorted(
            enumerate(records),
            key=lambda pair: (pair[1]["source_system"], pair[1]["event_id"], pair[0]),
        )
    ]
    with local_server() as (url, _):
        success = capture(engine, url + "/events")
        failed = capture(engine, url + "/events", fail_http_after=1)
    assert success["status"] == "SUCCEEDED"
    assert success["records"] == success["declared_items"] == 13
    assert success["pages"] == success["responses"] == 3
    assert failed["status"] == "FAILED"
    assert failed["error_category"] == "HTTP_ERROR"
    assert failed["records"] == 5
    assert failed["pages"] == 1 and failed["responses"] == 2
    with engine.connect() as connection:
        _, actual = recover(connection, success["run_id"])
        assert actual == expected
        failure_pages, actual = recover(connection, failed["run_id"])
        assert actual == expected[:5]
        assert failure_pages[-1].capture_status == "HTTP_ERROR"
        for report in (success, failed):
            row = connection.execute(
                text("SELECT status,error_category FROM ilc.runs WHERE run_id=:run"),
                {"run": report["run_id"]},
            ).one()
            assert row.status == report["status"]
            count = connection.execute(
                text("""
                SELECT count(*) FROM ilc.attempts a JOIN ilc.capture_items i USING(input_key)
                JOIN ilc.capture_pages p USING(page_key)
                WHERE a.run_id=:run AND p.run_id=:run AND a.outcome='ACCEPTED'
            """),
                {"run": report["run_id"]},
            ).scalar_one()
            assert count == report["records"]
    print("CAPTURE_RUNS", json.dumps([success, failed], default=str))


def test_page_transaction_rolls_back_on_late_error(engine):
    run_id = "rollback-probe-" + str(uuid4())
    started = now()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO ilc.sources VALUES ('synthetic_events','Synthetic') ON CONFLICT DO NOTHING"
            )
        )
        connection.execute(
            text(
                "INSERT INTO ilc.runs(run_id,stage,started_at,status) VALUES (:run,'API_CAPTURE_ROLLBACK_PROBE',:start,'RUNNING')"
            ),
            {"run": run_id, "start": started},
        )
    data = {
        "items": [{"source_system": "synthetic_events", "event_id": "probe"}],
        "dataset_id": "a" * 64,
        "total": 1,
        "next_cursor": None,
    }
    try:
        with engine.begin() as connection:
            write_page(
                connection,
                run_id,
                1,
                "synthetic_events",
                "http://127.0.0.1:8000/events",
                None,
                json.dumps(data).encode(),
                200,
                "application/json",
                started,
                data,
                None,
            )
            raise RuntimeError("Forced rollback after page and item inserts")
    except RuntimeError:
        pass
    with engine.begin() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM ilc.capture_pages WHERE run_id=:run"),
                {"run": run_id},
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                text("SELECT count(*) FROM ilc.attempts WHERE run_id=:run"),
                {"run": run_id},
            ).scalar_one()
            == 0
        )
        connection.execute(
            text(
                "UPDATE ilc.runs SET status='FAILED',ended_at=:end,error_category='EXPECTED_ROLLBACK_PROBE' WHERE run_id=:run"
            ),
            {"end": now(), "run": run_id},
        )

"""Contrato HTTP e reconciliacao com fixture independente da API."""

import json

import pytest
from fastapi.testclient import TestClient

from mock_api.app import FIXTURE, create_app, encode_cursor


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client


def expected_events():
    records = [json.loads(line) for line in FIXTURE.read_text().splitlines() if line]
    return [
        record
        for _, record in sorted(
            enumerate(records),
            key=lambda pair: (pair[1]["source_system"], pair[1]["event_id"], pair[0]),
        )
    ]


def test_first_middle_partial_and_end(client):
    expected = expected_events()
    pages = []
    cursor = None
    for start in (0, 5, 10):
        params = {"limit": 5}
        if cursor is not None:
            params["cursor"] = cursor
        response = client.get("/events", params=params)
        assert response.status_code == 200
        page = response.json()
        assert page["items"] == expected[start : start + 5]
        assert page["total"] == len(expected) == 13
        pages.append(page)
        cursor = page["next_cursor"]
    assert [len(page["items"]) for page in pages] == [5, 5, 3]
    assert [page["has_more"] for page in pages] == [True, True, False]
    assert cursor is None


@pytest.mark.parametrize("limit", [1, 2, 5, 13, 100])
def test_full_walk(client, limit):
    actual = []
    cursor = None
    seen = set()
    for _ in range(20):
        params = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        response = client.get("/events", params=params)
        assert response.status_code == 200
        page = response.json()
        actual.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            assert page["has_more"] is False
            break
        assert cursor not in seen
        seen.add(cursor)
    else:
        pytest.fail("Paginacao nao terminou")
    assert actual == expected_events()


def test_empty(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_bytes(b"")
    with TestClient(create_app(path)) as client:
        response = client.get("/events")
    assert response.status_code == 200
    page = response.json()
    assert page["items"] == []
    assert page["total"] == 0
    assert page["next_cursor"] is None
    assert page["has_more"] is False


@pytest.mark.parametrize("cursor", ["", "???", "e30", "W10", "A" * 257])
def test_malformed_cursor(client, cursor):
    response = client.get("/events", params={"cursor": cursor})
    assert response.status_code == (422 if len(cursor) > 256 else 400)


@pytest.mark.parametrize("offset", [-1, 0, 13, 14, True, "2"])
def test_invalid_offset(client, offset):
    dataset = client.get("/events").json()["dataset_id"]
    response = client.get("/events", params={"cursor": encode_cursor(dataset, offset)})
    assert response.status_code == 400
    assert response.json()["detail"] == "INVALID_CURSOR"


def test_other_dataset(client):
    assert (
        client.get("/events", params={"cursor": encode_cursor("wrong", 2)}).status_code
        == 400
    )


@pytest.mark.parametrize("limit", [0, -1, 101, "abc"])
def test_invalid_limit(client, limit):
    assert client.get("/events", params={"limit": limit}).status_code == 422


def test_openapi(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/events" in response.json()["paths"]
    assert "EventPage" in response.json()["components"]["schemas"]

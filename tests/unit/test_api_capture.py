"""Contrato de captura, sem conexao ao PostgreSQL."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts.api_capture import CaptureError, endpoint_url, validate_page

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures/synthetic/v1/valid/events.jsonl"
)


def page(items=None, **changes):
    data = {
        "items": [{"source_system": "synthetic_events", "event_id": "E1"}]
        if items is None
        else items,
        "total": 1,
        "dataset_id": "a" * 64,
        "next_cursor": None,
        "has_more": False,
    }
    data.update(changes)
    return json.dumps(data).encode()


def validate(raw, **kwargs):
    args = {
        "snapshot": None,
        "expected_total": None,
        "cursor": None,
        "seen": set(),
        "limit": 5,
        "source": "synthetic_events",
    }
    args.update(kwargs)
    return validate_page(raw, **args)


def test_preserves_all_fields_without_business_transform():
    item = {
        "source_system": "synthetic_events",
        "event_id": "E1",
        "unknown": "preserved",
        "occurred_at": None,
    }
    assert validate(page([item]))["items"] == [item]


def test_empty_explicit_end():
    assert validate(page([], total=0))["items"] == []


@pytest.mark.parametrize(
    "changes",
    [
        {"total": True},
        {"total": -1},
        {"total": 10001},
        {"items": {}},
        {"has_more": 1},
        {"dataset_id": "wrong"},
        {"next_cursor": "x"},
        {"has_more": True, "next_cursor": None},
        {"has_more": True, "next_cursor": ""},
    ],
)
def test_invalid_envelope(changes):
    with pytest.raises(CaptureError):
        validate(page(**changes))


@pytest.mark.parametrize("raw", [b"{", b"[]", b"null", b"{}", b"\xff"])
def test_invalid_json_or_shape(raw):
    with pytest.raises(CaptureError):
        validate(raw)


def test_snapshot_change():
    with pytest.raises(CaptureError, match="SNAPSHOT_CHANGED"):
        validate(page(), snapshot="b" * 64, expected_total=1)


def test_total_change():
    with pytest.raises(CaptureError, match="SNAPSHOT_CHANGED"):
        validate(page(), snapshot="a" * 64, expected_total=2)


def test_cycle():
    with pytest.raises(CaptureError, match="INVALID_TERMINATION"):
        validate(page(has_more=True, next_cursor="old"), seen={"old"})


@pytest.mark.parametrize(
    "item",
    [
        {},
        {"source_system": "other", "event_id": "E"},
        {"source_system": "synthetic_events", "event_id": " E"},
    ],
)
def test_invalid_provenance(item):
    with pytest.raises(CaptureError, match="INVALID_PROVENANCE"):
        validate(page([item]))


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:8000/events",
        "http://example.com/events",
        "http://127.0.0.1:8000/events?limit=1",
        "http://user:pass@127.0.0.1:8000/events",
        "http://127.0.0.1:bad/events",
    ],
)
def test_reject_nonlocal_or_ambiguous_url(url):
    with pytest.raises(ValueError):
        endpoint_url(url)


def test_local_url():
    assert (
        endpoint_url("http://127.0.0.1:8000/events") == "http://127.0.0.1:8000/events"
    )


def test_fixture_inventory():
    raw = FIXTURE.read_bytes()
    assert len([line for line in raw.splitlines() if line]) == 13
    assert len(hashlib.sha256(raw).hexdigest()) == 64

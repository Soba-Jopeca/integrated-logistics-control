"""Semantic identity and reproducible CSV references."""

import csv
import hashlib
import json

import pytest
from pydantic import ValidationError

from scripts.business_load import CSV_ROOT, FIXTURES, ROOT, normalize_event


def event():
    return {
        "schema_version": "1.0",
        "source_system": "synthetic_events",
        "event_id": "E",
        "delivery_id": "ENT-001",
        "event_type": "DELIVERED",
        "occurred_at": "2026-10-16T17:00:00Z",
    }


def test_timezone_and_optional_equivalence():
    original = event()
    alternative = {
        **original,
        "occurred_at": "2026-10-16T14:00:00-03:00",
        "notes": None,
    }
    assert normalize_event(original) == normalize_event(alternative)
    assert normalize_event(original)[0]["occurred_at"] == "2026-10-16T17:00:00.000000Z"


def test_property_order_equivalence():
    assert normalize_event(event()) == normalize_event(
        dict(reversed(list(event().items())))
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("event_id", " E"),
        ("event_id", ""),
        ("event_type", "FINISHED"),
        ("occurred_at", "2026-10-16T17:00:00"),
        ("notes", 123),
    ],
)
def test_invalid_contract(field, value):
    with pytest.raises(ValidationError):
        normalize_event({**event(), field: value})


def test_missing_reference_field():
    payload = event()
    del payload["delivery_id"]
    with pytest.raises(ValidationError):
        normalize_event(payload)


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        normalize_event({**event(), "unexpected": True})


def test_different_payload_changes_hash():
    assert (
        normalize_event(event())[1]
        != normalize_event({**event(), "occurred_at": "2026-10-16T17:10:00Z"})[1]
    )


@pytest.mark.parametrize("kind", ["orders", "deliveries"])
def test_csv_adapter_provenance_and_rows(kind):
    meta = json.loads((CSV_ROOT / "adapter.json").read_text())["files"][kind]
    raw = (CSV_ROOT / (kind + ".csv")).read_bytes()
    source = (ROOT / meta["source"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == meta["csv_sha256"]
    assert hashlib.sha256(source).hexdigest() == meta["source_sha256"]
    with (CSV_ROOT / (kind + ".csv")).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == meta["rows"] == 8
    original = [json.loads(line) for line in source.splitlines()]
    for actual, expected in zip(rows, original, strict=True):
        assert set(actual) == set(expected)
        for key, value in expected.items():
            assert (
                json.loads(actual[key]) if isinstance(value, dict) else actual[key]
            ) == (
                value
                if isinstance(value, dict)
                else ""
                if value is None
                else str(value)
            )


def test_fixture_event_classification_counts():
    paths = [
        "valid/events.jsonl",
        "replays/events.jsonl",
        "anomalies/events.jsonl",
        "invalid/events.jsonl",
    ]
    records = [
        [json.loads(line) for line in (FIXTURES / path).read_bytes().splitlines()]
        for path in paths
    ]
    assert list(map(len, records)) == [13, 1, 1, 3]
    identities = {}
    for item in records[0]:
        payload, fingerprint = normalize_event(item)
        assert (payload["source_system"], payload["event_id"]) not in identities
        identities[(payload["source_system"], payload["event_id"])] = fingerprint
    replay, sha = normalize_event(records[1][0])
    assert identities[(replay["source_system"], replay["event_id"])] == sha
    conflict, sha = normalize_event(records[2][0])
    assert identities[(conflict["source_system"], conflict["event_id"])] != sha
    for item in records[3]:
        with pytest.raises(ValidationError):
            normalize_event(item)

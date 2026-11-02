"""Retry policy tests; real HTTP/PostgreSQL scenarios live in reliability suite."""

import json

import httpx
import pytest

from scripts.api_capture import CaptureError, validate_page
from scripts.reliable_capture import request


def run_request(statuses):
    outcomes = iter(statuses)
    audit, delays = [], []

    def handle(req):
        item = next(outcomes)
        if isinstance(item, Exception):
            raise item
        status, body = item
        return httpx.Response(status, stream=httpx.ByteStream(body))

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = request(
            client,
            "http://127.0.0.1:8000/events",
            {},
            lambda *row: audit.append(row),
            sleep=delays.append,
        )
    return result, audit, delays


def test_transient_then_success():
    result, audit, delays = run_request([(503, b"busy"), (200, b"{}")])
    assert result == (200, b"{}")
    assert len(audit) == 2 and delays == [0.1]


@pytest.mark.parametrize("status", [408, 429, 500, 502, 503, 504])
def test_transient_status_retry_budget(status):
    records, delays = [], []

    def handle(req):
        return httpx.Response(status, stream=httpx.ByteStream(b"not available"))

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as client,
        pytest.raises(CaptureError, match="RETRY_EXHAUSTED"),
    ):
        request(
            client,
            "http://127.0.0.1:8000/events",
            {},
            lambda *row: records.append(row),
            sleep=delays.append,
        )
    assert len(records) == 3 and delays == [0.1, 0.2]
    assert all(row[1] == status and row[2] == b"not available" for row in records)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422])
def test_permanent_http_has_no_retry(status):
    _, audit, delays = run_request([(status, b"invalid")])
    assert len(audit) == 1 and delays == []


@pytest.mark.parametrize(
    "error_type", [httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout]
)
def test_transient_transport_recovery(error_type):
    _, audit, delays = run_request([error_type("controlled"), (200, b"{}")])
    assert audit[0][3] == error_type.__name__ and delays == [0.1]


def test_invalid_json_no_retry():
    (_, raw), audit, delays = run_request([(200, b"{")])
    with pytest.raises(CaptureError, match="INVALID_JSON"):
        validate_page(raw, None, None, None, set(), 5, "synthetic_events")
    assert len(audit) == 1 and delays == []


def test_snapshot_changed_not_transient():
    raw = json.dumps(
        {
            "items": [],
            "total": 0,
            "dataset_id": "b" * 64,
            "next_cursor": None,
            "has_more": False,
        }
    ).encode()
    with pytest.raises(CaptureError, match="SNAPSHOT_CHANGED"):
        validate_page(raw, "a" * 64, 0, None, set(), 5, "synthetic_events")

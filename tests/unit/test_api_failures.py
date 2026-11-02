"""Falhas reais com Uvicorn; sem ASGITransport/MockTransport nos cenarios."""

import pytest
from fastapi.testclient import TestClient

from mock_api.app import create_app
from scripts.check_api_failures import run


def test_real_http_failures_and_cleanup():
    report = run()
    assert report["verification"] == "PASS"
    assert report["child_stopped"] is True
    results = {item["scenario"]: item for item in report["results"]}
    assert results["delay"]["outcome"] == "READ_TIMEOUT"
    assert results["http_503"]["status"] == 503
    assert results["http_503"]["outcome"] == "HTTP_STATUS_ERROR"
    assert results["invalid_json"]["status"] == 200
    assert results["invalid_json"]["outcome"] == "JSON_DECODE_ERROR"
    assert results["server_stopped"]["outcome"] == "CONNECT_ERROR"


@pytest.mark.parametrize("seconds", [0, -1, 2.1, "nan", "inf", "abc"])
def test_delay_is_bounded(seconds):
    with TestClient(create_app()) as client:
        assert (
            client.get("/scenarios/delay", params={"seconds": seconds}).status_code
            == 422
        )


def test_failure_routes_documented():
    paths = create_app().openapi()["paths"]
    for route in ("delay", "http-503", "invalid-json"):
        assert "/scenarios/" + route in paths

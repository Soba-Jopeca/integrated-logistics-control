"""Explicit opt-in, all evidence retained on disposable case database."""

import os

import pytest

from scripts.check_reliability import run
from scripts.migration_config import TEST_DATABASE
from scripts.migration_config import test_engine as make_engine


def test_http_sql_reliability():
    capture = os.environ.get("ILC_RELIABILITY_CAPTURE_RUN")
    if os.environ.get("ILC_RELIABILITY_TEST_DATABASE") != TEST_DATABASE or not capture:
        pytest.skip("Explicit case database and original capture required")
    engine = make_engine(TEST_DATABASE)
    try:
        report = run(engine, capture)
        assert report["verification"] == "PASS"
        assert report["resume"]["records"] == 13
        assert report["reference_recovery"]["physical_state_after"] == "DELIVERED"
        print("RELIABILITY_RUNS", report)
    finally:
        engine.dispose()

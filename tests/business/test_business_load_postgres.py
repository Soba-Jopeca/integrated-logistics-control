"""Explicit database opt-in; preserve all runs and P02A evidence."""

import os

import pytest

from scripts.check_business_load import run
from scripts.migration_config import TEST_DATABASE
from scripts.migration_config import test_engine as make_engine


def test_business_load_real_postgres():
    capture_run = os.environ.get("ILC_BUSINESS_CAPTURE_RUN")
    if os.environ.get("ILC_BUSINESS_TEST_DATABASE") != TEST_DATABASE or not capture_run:
        pytest.skip("Explicit test database and capture run required")
    engine = make_engine(TEST_DATABASE)
    try:
        report = run(engine, capture_run)
        assert report["verification"] == "PASS"
        assert report["after"] == (8, 8, 13)
        assert report["capture_inputs_and_sentinel_preserved"] is True
        print("BUSINESS_RUNS", report)
    finally:
        engine.dispose()

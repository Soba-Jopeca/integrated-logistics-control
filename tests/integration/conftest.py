"""Documentary fixtures are always rolled back on the disposable database."""

import os

import pytest

from scripts.migration_config import TEST_DATABASE
from scripts.migration_config import test_engine as make_engine
from tests.integration.document_support import execute, seed_documents


@pytest.fixture
def document_connection():
    if os.environ.get("ILC_TEST_DATABASE") != TEST_DATABASE:
        pytest.fail("Set ILC_TEST_DATABASE=ilc_f2p02b_test explicitly")
    engine = make_engine(TEST_DATABASE)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                revision = execute(
                    connection, "SELECT version_num FROM public.alembic_version"
                ).scalar_one()
                if revision not in {"0002_documents", "0003_decisions_conflicts"}:
                    pytest.fail("Upgrade to 0002_documents before documentary probes")
                seed_documents(connection)
                yield connection
            finally:
                transaction.rollback()
    finally:
        engine.dispose()

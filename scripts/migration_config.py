"""Connections restricted to the explicitly selected disposable case database."""

from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import URL, create_engine
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE = "ilc_f2p02b_test"


def test_engine(database):
    """Never infer a DDL target from DB_NAME or process-wide PG variables."""
    if database != TEST_DATABASE:
        raise ValueError("An explicit disposable database target is required")
    config = dotenv_values(ROOT / ".env", interpolate=False)
    expected = {"DB_HOST": "127.0.0.1", "DB_PORT": "55432", "DB_USER": "ilc_app"}
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError("Unexpected case connection settings")
    if config.get("DB_NAME") != "ilc" or not config.get("DB_PASSWORD"):
        raise ValueError("Case configuration is incomplete")
    timeout_text = config.get("DB_CONNECT_TIMEOUT")
    if not timeout_text or not timeout_text.isdecimal():
        raise ValueError("Invalid connection timeout")
    timeout = int(timeout_text)
    if not 1 <= timeout <= 30:
        raise ValueError("Invalid connection timeout")
    url = URL.create(
        "postgresql+psycopg",
        host=config["DB_HOST"],
        port=int(config["DB_PORT"]),
        username=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=database,
    )
    return create_engine(
        url,
        poolclass=NullPool,
        echo=False,
        hide_parameters=True,
        connect_args={"connect_timeout": timeout},
    )

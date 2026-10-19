"""Verify the dedicated local PostgreSQL connection without exposing secrets."""

import json
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool


def main():
    root = Path(__file__).resolve().parents[1]
    if Path(sys.prefix).resolve() != (root / ".venv").resolve():
        raise RuntimeError("Unexpected Python environment")
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Virtual environment required")

    config = dotenv_values(root / ".env", interpolate=False)
    expected = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "55432",
        "DB_NAME": "ilc",
        "DB_USER": "ilc_app",
    }
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError("Unexpected database configuration")
    if not config.get("DB_PASSWORD"):
        raise ValueError("Missing password")
    timeout = int(config["DB_CONNECT_TIMEOUT"])
    if not 1 <= timeout <= 30:
        raise ValueError("Invalid timeout")

    url = URL.create(
        "postgresql+psycopg",
        host=config["DB_HOST"],
        port=int(config["DB_PORT"]),
        database=config["DB_NAME"],
        username=config["DB_USER"],
        password=config["DB_PASSWORD"],
    )
    engine = create_engine(
        url,
        echo=False,
        hide_parameters=True,
        poolclass=NullPool,
        connect_args={"connect_timeout": timeout},
    )
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            result = dict(
                connection.execute(
                    text("""
                SELECT current_user AS db_user,
                       current_database() AS db_name,
                       current_setting('server_version') AS server_version,
                       host(inet_server_addr()) AS server_address,
                       inet_server_port() AS server_port,
                       current_setting('TimeZone') AS timezone,
                       r.rolsuper, r.rolcreatedb, r.rolcreaterole,
                       r.rolreplication, r.rolbypassrls,
                       r.rolconnlimit,
                       pg_get_userbyid(d.datdba) AS database_owner
                FROM pg_roles r
                JOIN pg_database d ON d.datname = current_database()
                WHERE r.rolname = current_user
            """)
                )
                .mappings()
                .one()
            )
            if result["db_user"] != "ilc_app" or result["db_name"] != "ilc":
                raise RuntimeError("Unexpected database identity")
            restricted = (
                "rolsuper",
                "rolcreatedb",
                "rolcreaterole",
                "rolreplication",
                "rolbypassrls",
            )
            if any(result[key] for key in restricted):
                raise RuntimeError("Unexpected administrative privileges")
            if result["server_address"] != "127.0.0.1":
                raise RuntimeError("Unexpected server address")
            if result["server_port"] != 55432:
                raise RuntimeError("Unexpected server port")
            print(json.dumps(result, indent=2))
            print("SQLAlchemy + psycopg connection: PASS")
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (SQLAlchemyError, OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"Connection check: FAIL ({type(error).__name__})")
        safe_messages = {
            "Unexpected Python environment",
            "Virtual environment required",
            "Unexpected database configuration",
            "Missing password",
            "Invalid timeout",
            "Unexpected database identity",
            "Unexpected administrative privileges",
            "Unexpected server address",
            "Unexpected server port",
        }
        if str(error) in safe_messages:
            print("Reason:", str(error))
        sys.exit(1)

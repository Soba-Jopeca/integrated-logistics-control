"""Inspect migration state without changing the disposable database."""

import argparse
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from scripts.migration_config import TEST_DATABASE, test_engine

TABLES = {
    "sources",
    "inputs",
    "receipts",
    "runs",
    "attempts",
    "orders",
    "deliveries",
    "events",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--expect", required=True, choices=["base", "head"])
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        with engine.connect() as connection:
            catalog = inspect(connection)
            schema_exists = "ilc" in catalog.get_schema_names()
            tables = (
                set(catalog.get_table_names(schema="ilc")) if schema_exists else set()
            )
            revisions = []
            if catalog.has_table("alembic_version", schema="public"):
                revisions = list(
                    connection.execute(
                        text("SELECT version_num FROM public.alembic_version")
                    ).scalars()
                )
            if args.expect == "base":
                valid = not schema_exists and not revisions
            else:
                valid = (
                    schema_exists and tables == TABLES and revisions == ["0001_core"]
                )
            print("Database:", args.database)
            print("Domain tables:", ", ".join(sorted(tables)) or "none")
            print("Revision:", ", ".join(revisions) or "base")
            if not valid:
                raise RuntimeError("Unexpected schema or revision")
            print("Migration state: PASS (" + args.expect + ")")
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (SQLAlchemyError, OSError, ValueError, RuntimeError) as error:
        print(f"Migration state: FAIL ({type(error).__name__})")
        sys.exit(1)

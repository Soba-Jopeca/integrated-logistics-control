"""Inspect the exact catalog for base, core or documentary migration state."""

import argparse
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from scripts.migration_config import TEST_DATABASE, test_engine

CORE_TABLES = {
    "sources",
    "inputs",
    "receipts",
    "runs",
    "attempts",
    "orders",
    "deliveries",
    "events",
}
DOCUMENT_TABLES = {
    "document_families",
    "document_versions",
    "extractions",
    "evaluations",
    "evaluation_reasons",
    "document_validities",
    "evaluation_validities",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--expect", required=True, choices=["base", "core", "head"])
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        with engine.connect() as connection:
            catalog = inspect(connection)
            schemas = catalog.get_schema_names()
            tables = (
                set(catalog.get_table_names(schema="ilc"))
                if "ilc" in schemas
                else set()
            )
            revisions = []
            if catalog.has_table("alembic_version", schema="public"):
                revisions = list(
                    connection.execute(
                        text("SELECT version_num FROM public.alembic_version")
                    ).scalars()
                )
            extension = connection.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'btree_gist'")
            ).scalar_one_or_none()
            extra_unique = False
            if "events" in tables:
                extra_unique = any(
                    c["name"] == "uq_events_key_delivery_type"
                    for c in catalog.get_unique_constraints("events", schema="ilc")
                )
            if args.expect == "base":
                valid = (
                    "ilc" not in schemas
                    and not revisions
                    and extension is None
                    and "ilc_gist" not in schemas
                )
            elif args.expect == "core":
                valid = (
                    tables == CORE_TABLES
                    and revisions == ["0001_core"]
                    and extension is None
                    and not extra_unique
                    and "ilc_gist" not in schemas
                )
            else:
                valid = (
                    tables == CORE_TABLES | DOCUMENT_TABLES
                    and revisions == ["0002_documents"]
                    and extension is not None
                    and extra_unique
                    and "ilc_gist" in schemas
                )
            print("Database:", args.database)
            print("Domain tables:", ", ".join(sorted(tables)) or "none")
            print("Revision:", ", ".join(revisions) or "base")
            print("btree_gist:", extension or "not installed")
            if not valid:
                raise RuntimeError("Unexpected schema, extension or revision")
            print("Migration state: PASS (" + args.expect + ")")
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (SQLAlchemyError, OSError, ValueError, RuntimeError) as error:
        print(f"Migration state: FAIL ({type(error).__name__})")
        sys.exit(1)

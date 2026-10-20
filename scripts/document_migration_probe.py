"""Preserve a synthetic core source across the documentary downgrade cycle."""

import argparse
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from scripts.migration_config import TEST_DATABASE, test_engine

SOURCE = "__p02c_preservation__"
DESCRIPTION = "Synthetic source retained across documentary migration cycle"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--initialize", action="store_true")
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        with engine.begin() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar_one()
            if revision not in {
                "0001_core",
                "0002_documents",
                "0003_decisions_conflicts",
            }:
                raise RuntimeError("Unexpected revision")
            if args.initialize and revision != "0001_core":
                raise RuntimeError(
                    "Initialize the sentinel before the documentary upgrade"
                )
            description = connection.execute(
                text(
                    "SELECT description FROM ilc.sources WHERE source_system = :source"
                ),
                {"source": SOURCE},
            ).scalar_one_or_none()
            if description is None and args.initialize:
                connection.execute(
                    text(
                        "INSERT INTO ilc.sources (source_system, description) VALUES (:source, :description)"
                    ),
                    {"source": SOURCE, "description": DESCRIPTION},
                )
                description = DESCRIPTION
            if description != DESCRIPTION:
                raise RuntimeError("Core sentinel is missing or has changed")
            print("Core sentinel preserved: PASS (" + revision + ")")
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except (SQLAlchemyError, OSError, ValueError, RuntimeError) as error:
        print(f"Core sentinel: FAIL ({type(error).__name__})")
        sys.exit(1)

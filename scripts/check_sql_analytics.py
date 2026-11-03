"""Run isolated PostgreSQL analytical queries; rollback all temporary objects."""

import argparse
import json
import math
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import text

from scripts.migration_config import test_engine as make_engine

SQL = Path(__file__).resolve().parents[1] / "analytics" / "sql"
EXPECTED = {
    "m1": dict(eligible=4, on_time=3, missing_promise=1, contested=1, rate_pct=75),
    "m2": dict(completed=6, missing_document=2),
    "m3": dict(review_required=1, not_evaluated=1),
    "m4": dict(eligible=2, missing_valid=2, negative=1, contested=1, median_hours=1 / 12),
}


def load(connection, name):
    # Repository-owned SQL consists of simple semicolon-separated statements.
    for statement in (SQL / name).read_text(encoding="utf-8").strip().rstrip(";").split(";"):
        connection.exec_driver_sql(statement)


def report(connection, prepared):
    names = ("m2", "m3", "m4") if prepared else tuple(EXPECTED)
    return {
        name: dict(connection.exec_driver_sql((SQL / f"{name}.sql").read_text()).mappings().one())
        for name in names
    }


def check(actual, expected):
    for metric, row in actual.items():
        assert row.keys() == expected[metric].keys(), (metric, row)
        for key, value in row.items():
            target = expected[metric][key]
            if target is None:
                assert value is None, (metric, key, value)
            else:
                assert value is not None and math.isclose(value, target), (
                    metric, key, target, value,
                )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--mode", choices=("fixture", "operational"), default="fixture")
    parser.add_argument("--prepared", action="store_true", help="Skip author exercise M1")
    parser.add_argument("--cutoff", type=datetime.fromisoformat)
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    args = parser.parse_args()
    if args.mode == "operational" and not all((args.start, args.end, args.cutoff)):
        parser.error("operational mode requires --start, --end and --cutoff")
    start = args.start or date(2026, 10, 16)
    end = args.end or date(2026, 10, 17)
    cutoff = args.cutoff or datetime.fromisoformat("2026-10-17T12:00:00+00:00")
    if args.mode == "fixture" and any((args.start, args.end, args.cutoff)):
        parser.error("fixture uses fixed inputs")
    if start >= end or cutoff.utcoffset() is None:
        parser.error("Use start < end and a cutoff with an explicit offset")

    engine = make_engine(args.database)
    try:
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            try:
                connection.execute(text("""
                    CREATE TEMP TABLE reference (
                        reference_key text PRIMARY KEY, cutoff timestamptz NOT NULL,
                        period_start date NOT NULL, period_end date NOT NULL,
                        zone text NOT NULL, publication text NOT NULL,
                        queried_at timestamptz NOT NULL
                    ) ON COMMIT DROP
                """))
                connection.execute(text("""
                    INSERT INTO reference VALUES (
                        :key, :cutoff, :start, :end, 'America/Sao_Paulo',
                        'f5-p02-v1', transaction_timestamp()
                    )
                """), dict(key=f"f5-p02-v1/{cutoff.isoformat()}/{start}/{end}", cutoff=cutoff,
                           start=start, end=end))
                load(connection, f"01-{args.mode}.sql")
                load(connection, "02-facts.sql")
                actual = report(connection, args.prepared)
                print(json.dumps({"mode": args.mode, "reference": dict(
                    connection.execute(text("SELECT * FROM reference")).mappings().one()
                ), "observed": actual}, default=str, indent=2))
                if args.mode == "fixture":
                    check(actual, EXPECTED)
                    assert connection.execute(text("SELECT count(*) FROM fixture_reasons")).scalar_one() == 2
                    assert connection.execute(text("SELECT count(*) FROM fact_document_reference WHERE document_key IN ('A1','FUTURE')")).scalar_one() == 0
                    assert connection.execute(text("SELECT count(*) FROM fact_delivery_reference WHERE delivery_id='F5-P02-E1'")).scalar_one() == 1
                    connection.execute(text("""
                        UPDATE reference SET period_start='2026-10-20', period_end='2026-10-21'
                    """))
                    empty = report(connection, args.prepared)
                    check(empty, dict(EXPECTED,
                        m1=dict(eligible=0, on_time=0, missing_promise=0, contested=0, rate_pct=None),
                        m4=dict(eligible=0, missing_valid=0, negative=0, contested=0, median_hours=None),
                    ))
                    print("PASS: expected results, empty cohort, grain and validity")
            finally:
                connection.rollback()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

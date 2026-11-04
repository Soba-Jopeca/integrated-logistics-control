"""Export the F5-P02 synthetic fixture and SQL results for local Power BI."""

import argparse
import csv
import json
from pathlib import Path

from scripts.check_sql_analytics import EXPECTED, check, load, report
from scripts.migration_config import test_engine as make_engine


def collect(connection, variant="base"):
    connection.exec_driver_sql("""
        CREATE TEMP TABLE reference AS SELECT
          'f5-p02-v1/2026-10-17T12:00:00+00:00/2026-10-16/2026-10-17'::text AS reference_key,
          '2026-10-17 12:00Z'::timestamptz AS cutoff,
          DATE '2026-10-16' AS period_start, DATE '2026-10-17' AS period_end,
          'America/Sao_Paulo'::text AS zone, 'f5-p02-v1'::text AS publication,
          transaction_timestamp() AS queried_at
    """)
    load(connection, "01-fixture.sql")
    if variant == "alternate":
        connection.exec_driver_sql("ALTER VIEW src_delivery RENAME TO src_delivery_base")
        connection.exec_driver_sql("""
            CREATE TEMP VIEW src_delivery AS
            SELECT delivery_key, delivery_id || '-ALT' AS delivery_id,
                   order_key, order_id, released_at, promised_at
            FROM src_delivery_base
        """)
    load(connection, "02-facts.sql")
    ref = dict(connection.exec_driver_sql("SELECT * FROM reference").mappings().one())
    scenarios = {
        "BASE": ("TRUE", EXPECTED),
        "EMPTY": ("FALSE", dict(EXPECTED,
            m1=dict(eligible=0, on_time=0, missing_promise=0, contested=0, rate_pct=None),
            m4=dict(eligible=0, missing_valid=0, negative=0, contested=0, median_hours=None))),
        "LATE": ("f.delivery_key = '2'", dict(EXPECTED,
            m1=dict(eligible=1, on_time=0, missing_promise=0, contested=0, rate_pct=0),
            m4=dict(eligible=0, missing_valid=0, negative=1, contested=0, median_hours=None))),
    }
    output = {}
    reference = {}
    for scenario, (predicate, expected) in scenarios.items():
        # Predicates are fixed repository constants, never command-line input.
        connection.exec_driver_sql(f"""
            CREATE OR REPLACE TEMP VIEW completion_cohort AS
            SELECT f.* FROM fact_delivery_reference f JOIN reference r USING (reference_key)
            WHERE f.completed_local_date >= r.period_start
              AND f.completed_local_date < r.period_end AND ({predicate})
        """)
        reference[scenario] = report(connection, False)
        check(reference[scenario], expected)
        queries = {
            "deliveries": """SELECT f.*, c.delivery_key IS NOT NULL AS in_cohort
                FROM fact_delivery_reference f LEFT JOIN completion_cohort c
                USING (reference_key, delivery_key) ORDER BY f.delivery_key""",
            "documents": "SELECT * FROM fact_document_reference ORDER BY document_key",
        }
        for name, sql in queries.items():
            result = connection.exec_driver_sql(sql)
            columns, rows = output.setdefault(name, (["scenario", *result.keys()], []))
            rows.extend((scenario, *row) for row in result)

    dimensions = (
        "dim_delivery", "dim_document", "dim_date", "dim_source", "dim_result",
        "dim_reason", "dim_rules", "fact_evaluation_history", "bridge_evaluation_reason",
    )
    for name in dimensions:
        result = connection.exec_driver_sql(f"SELECT * FROM {name} ORDER BY 1")
        output[name] = (list(result.keys()), result.fetchall())
    output["scenarios"] = (["scenario"], [(name,) for name in scenarios])
    return ref, reference, output


def export(connection, out):
    ref, reference, output = collect(connection)
    out.mkdir(parents=True, exist_ok=True)
    for name, (columns, rows) in output.items():
        with (out / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(columns)
            writer.writerows(rows)
    (out / "sql-reference.json").write_text(
        json.dumps({"reference": ref, "scenarios": reference}, default=str, indent=2),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    engine = make_engine(args.database)
    try:
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
            try:
                export(conn, args.out)
            finally:
                conn.rollback()
    finally:
        engine.dispose()
    print(f"PASS: SQL reference and Power BI fixture exported to {args.out}")


if __name__ == "__main__":
    main()

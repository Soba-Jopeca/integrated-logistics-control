"""Publish and verify the synthetic Gold fixture on the dedicated test database."""

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text

from scripts.check_sql_analytics import SQL, check
from scripts.export_powerbi_fixture import collect
from scripts.migration_config import test_engine as make_engine


class QualityError(ValueError):
    """Safe diagnostic category for the controlled failure."""


def insert(conn, table, rows):
    if not rows:
        return
    columns = ", ".join(rows[0])
    binds = ", ".join(":" + key for key in rows[0])
    conn.execute(text(f"INSERT INTO analytics.{table} ({columns}) VALUES ({binds})"), rows)


def metric_results(conn, publication_id, scenario):
    cohort = "(SELECT * FROM analytics.deliveries WHERE publication_id=:pid AND scenario=:scenario"
    sources = {
        "completion_cohort": cohort + " AND in_cohort) AS completion_cohort",
        "fact_delivery_reference": cohort + ") AS fact_delivery_reference",
        "fact_document_reference": "(SELECT * FROM analytics.documents "
        "WHERE publication_id=:pid AND scenario=:scenario) AS fact_document_reference",
    }
    results = {}
    for name in ("m1", "m2", "m3", "m4"):
        sql = (SQL / f"{name}.sql").read_text(encoding="utf-8")
        sql = re.sub(
            r"(?im)\bFROM (completion_cohort|fact_delivery_reference|fact_document_reference)\b",
            lambda match: "FROM " + sources[match[1]], sql,
        )
        results[name] = dict(conn.execute(text(sql), dict(pid=publication_id, scenario=scenario))
                             .mappings().one())
    return results


def rows_for(output, name, pid):
    columns, rows = output[name]
    return [dict(publication_id=pid, **dict(zip(columns, row, strict=True))) for row in rows]


def publish(engine, variant, force_failure):
    run = uuid4()
    started = datetime.now(UTC)
    pid = None
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            ref, expected, output = collect(conn, variant)
            rules_hash = hashlib.sha256(b"".join(
                p.read_bytes() for p in sorted(SQL.glob("0*.sql")) + sorted(SQL.glob("m[1-4].sql"))
            )).hexdigest()
            ref.pop("queried_at")
            pid = hashlib.sha256(json.dumps(
                [ref, rules_hash, {
                    name: (cols, sorted(rows, key=lambda row: json.dumps(row, default=str)))
                    for name, (cols, rows) in output.items()
                }], sort_keys=True, default=str
            ).encode()).hexdigest()
            created = conn.execute(text("""
                INSERT INTO analytics.publication
                (publication_id, reference_key, cutoff, period_start, period_end, zone, rules_hash)
                VALUES (:pid, :reference_key, :cutoff, :period_start, :period_end, :zone, :rules_hash)
                ON CONFLICT DO NOTHING RETURNING publication_id
            """), dict(pid=pid, rules_hash=rules_hash, **{
                k: v for k, v in ref.items() if k != "publication"
            })).scalar()
            deliveries = rows_for(output, "deliveries", pid)
            documents = rows_for(output, "documents", pid)
            dim_cols, dim_rows = output["dim_document"]
            dims = {r[0]: dict(zip(dim_cols, r, strict=True)) for r in dim_rows}
            reasons = []
            for row in documents:
                row.pop("reference_key")
                row.update({k: dims[row["document_key"]][k]
                            for k in ("document_id", "family_key", "version")})
                for evaluation_key, code, field in output["bridge_evaluation_reason"][1]:
                    if evaluation_key == row["evaluation_key"]:
                        reasons.append({k: row[k] for k in
                            ("publication_id", "scenario", "document_key", "evaluation_key")}
                            | dict(code=code, affected_field=field))
            for row in deliveries:
                row.pop("reference_key")
            if created:
                insert(conn, "scenarios", rows_for(output, "scenarios", pid))
                insert(conn, "deliveries", deliveries)
                insert(conn, "documents", documents)
                insert(conn, "reasons", reasons)
            counts = {}
            for table, rows in (("deliveries", deliveries), ("documents", documents), ("reasons", reasons)):
                counts[table] = conn.execute(text(
                    f"SELECT count(*) FROM analytics.{table} WHERE publication_id=:pid"
                ), {"pid": pid}).scalar_one()
                if counts[table] != len(rows):
                    raise QualityError("ROW_COUNT_MISMATCH")
            invalid = conn.execute(text("""
                SELECT EXISTS (SELECT 1 FROM analytics.documents WHERE publication_id=:pid
                    AND document_key IN ('A1', 'FUTURE'))
                   OR EXISTS (SELECT 1 FROM analytics.reasons WHERE publication_id=:pid
                    AND document_key <> 'B1')
            """), {"pid": pid}).scalar_one()
            if invalid or counts["reasons"] != 6:
                raise QualityError("VIGENCY_OR_REASON_MISMATCH")
            actual = {scenario: metric_results(conn, pid, scenario) for scenario in expected}
            for scenario in expected:
                check(actual[scenario], expected[scenario])
            if force_failure:
                raise QualityError("CONTROLLED_QUALITY_FAILURE")
            status = "PUBLISHED" if created else "REUSED"
            insert(conn, "runs", [dict(run_id=run, publication_id=pid,
                                      started_at=started, status=status)])
            evidence = dict(run_id=run, publication_id=pid, status=status, reference=ref,
                            counts=counts, expected=expected, observed=actual,
                            sample_delivery=deliveries[0],
                            sample_document=next(r for r in documents if r["document_key"] == "B1"))
        return evidence
    except Exception as exc:
        diagnostic = str(exc) if isinstance(exc, QualityError) else type(exc).__name__
        with engine.begin() as conn:
            insert(conn, "runs", [dict(run_id=run, started_at=started,
                                      status="FAILED", diagnostic=diagnostic,
                                      attempted_publication_id=pid)])
            remaining = conn.execute(text("""
                SELECT count(*) FROM analytics.consume_publication
            """)).scalar_one()
            visible = conn.execute(text("""
                SELECT EXISTS (SELECT 1 FROM analytics.consume_publication WHERE publication_id=:pid)
            """), {"pid": pid}).scalar_one()
        return dict(run_id=run, attempted_publication_id=pid, status="FAILED",
                    diagnostic=diagnostic, published_count=remaining, attempted_visible=visible)


def prove(engine):
    first = publish(engine, "base", False)
    replay = publish(engine, "base", False)
    alternate = publish(engine, "alternate", False)
    failure = publish(engine, "failure", True)
    assert first["status"] in {"PUBLISHED", "REUSED"}, first
    assert replay["status"] == "REUSED" and replay["publication_id"] == first["publication_id"]
    assert replay["counts"] == first["counts"] and replay["run_id"] != first["run_id"]
    assert alternate["status"] in {"PUBLISHED", "REUSED"}, alternate
    assert alternate["publication_id"] != first["publication_id"]
    assert alternate["reference"]["cutoff"] == first["reference"]["cutoff"]
    assert alternate["sample_delivery"]["delivery_id"].endswith("-ALT")
    assert failure["diagnostic"] == "CONTROLLED_QUALITY_FAILURE"
    assert not failure["attempted_visible"]
    with engine.connect() as conn:
        ids = dict(base=first["publication_id"], alt=alternate["publication_id"],
                   failed=failure["attempted_publication_id"], run=failure["run_id"])
        for table, count in first["counts"].items():
            observed = conn.execute(text(f"""
                SELECT count(*) FILTER (WHERE publication_id=:base),
                       count(*) FILTER (WHERE publication_id=:alt),
                       count(*) FILTER (WHERE publication_id=:failed)
                FROM analytics.consume_{table}
            """), ids).one()
            assert tuple(observed) == (count, count, 0)
        persisted = conn.execute(text("""
            SELECT diagnostic FROM analytics.runs WHERE run_id=:run
              AND status='FAILED' AND attempted_publication_id=:failed
        """), ids).scalar_one()
        assert persisted == failure["diagnostic"]
    return dict(first=first, replay=replay, alternate=alternate, failure=failure,
                verdict="PASS: reuse, versioning, rollback and retained diagnostic")



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--variant", choices=("base", "alternate", "failure"), default="base")
    parser.add_argument("--prove", action="store_true")
    args = parser.parse_args()
    engine = make_engine(args.database)
    try:
        if args.prove:
            print(json.dumps(prove(engine), default=str, indent=2))
            return 0
        evidence = publish(engine, args.variant, args.variant == "failure")
        print(json.dumps(evidence, default=str, indent=2))
        return int(evidence["status"] == "FAILED")
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

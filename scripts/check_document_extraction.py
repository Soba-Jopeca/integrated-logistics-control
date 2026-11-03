"""Run only after the author's transformation, against the explicit test DB."""

import argparse
import hashlib
import json
from pathlib import Path

from scripts.migration_config import test_engine
from src.documents.service import extract_document, sql

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures/documents/v1"


def run(engine):
    expected = json.loads((FIXTURES / "expected.json").read_text())
    reports = []
    with engine.connect() as c:
        evaluations_before = sql(c, "SELECT count(*) FROM ilc.evaluations").scalar_one()
        assert (
            sql(c, "SELECT version_num FROM public.alembic_version").scalar_one()
            == "0006_reliability"
        )
        assert (
            sql(
                c, "SELECT count(*) FROM ilc.deliveries WHERE delivery_id='ENT-001'"
            ).scalar_one()
            == 1
        )
    for name, result in expected.items():
        stem = name.replace(".", "-").upper()
        env = {
            "schema_version": "1.0",
            "source_system": "synthetic_documents_p01",
            "document_id": "F4-P01-" + stem,
            "document_family_id": "F4-P01-FAMILY-" + stem,
            "version": 1,
            "supersedes_document_id": None,
            "delivery_id": "ENT-001",
            "media_type": "application/pdf"
            if name.endswith(".pdf")
            else "application/xml",
        }
        first = extract_document(engine, FIXTURES / name, env)
        second = extract_document(engine, FIXTURES / name, env)
        assert first["document_key"] == second["document_key"]
        assert first["input_key"] == second["input_key"]
        assert first["extraction_key"] != second["extraction_key"]
        assert second["duplicate"] is True
        assert (
            first["file_sha256"]
            == hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
        )
        if isinstance(result, str):
            assert first["error_category"] == second["error_category"] == result
        else:
            normalized = json.loads(
                json.dumps(
                    second["fields"],
                    default=lambda x: x.isoformat().replace("+00:00", "Z"),
                )
            )
            assert normalized == result
        with engine.connect() as c:
            row = (
                sql(
                    c,
                    """SELECT d.file_reference,d.file_sha256,i.original_sha256,i.received_at,
                count(x.extraction_key) AS extractions FROM ilc.document_versions d
                JOIN ilc.inputs i USING(input_key) JOIN ilc.extractions x USING(document_key,input_key)
                WHERE d.document_key=:key GROUP BY d.document_key,i.input_key""",
                    key=first["document_key"],
                )
                .mappings()
                .one()
            )
            assert (
                hashlib.sha256(Path(row["file_reference"]).read_bytes()).hexdigest()
                == row["file_sha256"]
                == row["original_sha256"]
            )
            assert row["extractions"] >= 2 and row["received_at"] is not None
        reports.extend([first, second])
    missing = extract_document(engine, FIXTURES / "absent.xml", env)
    assert missing["error_category"] == "FILE_MISSING"
    env = dict(
        env,
        document_id="F4-P01-UNSUPPORTED",
        document_family_id="F4-P01-UNSUPPORTED",
        media_type="text/plain",
    )
    unsupported = extract_document(engine, FIXTURES / "valid.xml", env)
    assert unsupported["error_category"] == "UNSUPPORTED_FORMAT"
    with engine.connect() as c:
        assert (
            sql(c, "SELECT count(*) FROM ilc.evaluations").scalar_one()
            == evaluations_before
        )
        count = sql(
            c,
            "SELECT count(*) FROM ilc.document_versions WHERE source_system='synthetic_documents_p01'",
        ).scalar_one()
        assert count == len(expected)
    return {
        "verification": "PASS",
        "document_versions": count,
        "reports": reports,
        "missing": missing,
        "unsupported": unsupported,
        "evaluations_unchanged": True,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database", required=True)
    args = p.parse_args()
    engine = test_engine(args.database)
    try:
        print(json.dumps(run(engine), default=str))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

"""P02 isolated synthetic references; preserve all previous case evidence."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from scripts.migration_config import test_engine
from src.documents.service import extract_document, sql
from src.documents.validation import evaluate, regularity

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures/documents/p02"
SOURCE = "synthetic_documents_p02"


def key(label):
    return uuid5(NAMESPACE_URL, "ilc-f4-p02:" + label)


def seed(engine):
    with engine.begin() as c:
        sql(c, "SELECT pg_advisory_xact_lock(4040101)")
        now = datetime.now(UTC)
        sql(
            c,
            "INSERT INTO ilc.sources VALUES (:source,'P02 synthetic verification only') ON CONFLICT DO NOTHING",
            source=SOURCE,
        )
        sql(
            c,
            "INSERT INTO ilc.runs VALUES ('f4-p02-fixture','SYNTHETIC_P02',:now,:now,'SUCCEEDED',NULL) ON CONFLICT DO NOTHING",
            now=now,
        )
        for name in (
            "AB",
            "UNCONFIRMED",
            "CONTESTED",
            "MISSING",
            "REFERENCE",
            "TIME",
            "UNIT",
        ):
            delivery = key("delivery:" + name)
            sql(
                c,
                "INSERT INTO ilc.orders VALUES (:key,:source,:id,'2026-10-16T10:00:00Z','{}') ON CONFLICT DO NOTHING",
                key=key("order:" + name),
                source=SOURCE,
                id="F4-P02-ORDER-" + name,
            )
            sql(
                c,
                "INSERT INTO ilc.deliveries VALUES (:key,:order,:id,'2026-10-16T18:00:00Z',10,'VOLUME') ON CONFLICT DO NOTHING",
                key=delivery,
                order=key("order:" + name),
                id="F4-P02-" + name,
            )
            row = (
                sql(
                    c,
                    "SELECT * FROM ilc.deliveries WHERE delivery_key=:key",
                    key=delivery,
                )
                .mappings()
                .one()
            )
            assert row["expected_quantity"] == 10 and row["quantity_unit"] == "VOLUME"
            if name == "UNCONFIRMED":
                continue
            for sequence in range(1, 3 if name == "CONTESTED" else 2):
                label = name + str(sequence)
                event, input_key, attempt = (
                    key("event:" + label),
                    key("input:" + label),
                    key("attempt:" + label),
                )
                digest = hashlib.sha256(label.encode()).hexdigest()
                sql(
                    c,
                    """INSERT INTO ilc.inputs VALUES (:key,:source,'EVENT',:id,'synthetic://p02',:hash,:now,:hash,'fixture-v1',NULL) ON CONFLICT DO NOTHING""",
                    key=input_key,
                    source=SOURCE,
                    id=label,
                    hash=digest,
                    now=now,
                )
                sql(
                    c,
                    "INSERT INTO ilc.attempts VALUES (:key,:input,'f4-p02-fixture',NULL,:now,:now,'ACCEPTED',NULL) ON CONFLICT DO NOTHING",
                    key=attempt,
                    input=input_key,
                    now=now,
                )
                occurred = datetime(
                    2026, 10, 16, 17, 0 if sequence == 1 else 10, tzinfo=UTC
                )
                sql(
                    c,
                    """INSERT INTO ilc.events
                    (event_key,source_system,event_id,delivery_key,schema_version,event_type,occurred_at,input_key,accepted_attempt_id,accepted_at,acceptance_sequence)
                    VALUES (:key,:source,:id,:delivery,'1.0','DELIVERED',:time,:input,:attempt,:now,:sequence) ON CONFLICT DO NOTHING""",
                    key=event,
                    source=SOURCE,
                    id=label,
                    delivery=delivery,
                    time=occurred,
                    input=input_key,
                    attempt=attempt,
                    now=now,
                    sequence=sequence,
                )
            sql(
                c,
                """INSERT INTO ilc.completion_decisions
                (completion_decision_key,delivery_key,event_key,decision_number,decided_at,decision_type,author,reason)
                VALUES (:key,:delivery,:event,1,:now,'PROVISIONAL','fixture:p02','SYNTHETIC_FIRST_ACCEPTANCE') ON CONFLICT DO NOTHING""",
                key=key("decision:" + name),
                delivery=delivery,
                event=key("event:" + name + "1"),
                now=now,
            )
            if name == "CONTESTED":
                conflict = key("conflict")
                sql(
                    c,
                    "INSERT INTO ilc.conflicts VALUES (:key,:delivery,'COMPLETION_AMBIGUITY',:now,'P02 synthetic ambiguity') ON CONFLICT DO NOTHING",
                    key=conflict,
                    delivery=delivery,
                    now=now,
                )
                for sequence, role in [(1, "ORIGINAL"), (2, "ALTERNATIVE")]:
                    sql(
                        c,
                        """INSERT INTO ilc.conflict_evidence VALUES (:key,:conflict,:input,:event,NULL,:role,:now) ON CONFLICT DO NOTHING""",
                        key=key("evidence:" + str(sequence)),
                        conflict=conflict,
                        input=key("input:" + name + str(sequence)),
                        event=key("event:" + name + str(sequence)),
                        role=role,
                        now=now,
                    )


def snapshot(engine):
    with engine.begin() as c:
        sql(c, "SET TRANSACTION READ ONLY")
        physical = {
            table: sql(
                c,
                f"SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]'::jsonb) FROM (SELECT to_jsonb(t) AS v FROM ilc.{table} t) s",
            ).scalar_one()
            for table in (
                "events",
                "deliveries",
                "completion_decisions",
                "conflicts",
                "conflict_resolutions",
            )
        }
        p01 = sql(
            c,
            """SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]'::jsonb) FROM (
            SELECT to_jsonb(d) AS v FROM ilc.document_versions d WHERE source_system='synthetic_documents_p01'
            UNION ALL SELECT to_jsonb(x) FROM ilc.extractions x JOIN ilc.document_versions d USING(document_key) WHERE d.source_system='synthetic_documents_p01') s""",
        ).scalar_one()
        return physical, p01


def envelope(name, delivery="AB", family=None, version=1, previous=None):
    return {
        "schema_version": "1.0",
        "source_system": SOURCE,
        "document_id": "F4-P02-" + name,
        "document_family_id": "F4-P02-" + (family or name),
        "version": version,
        "supersedes_document_id": "F4-P02-" + previous if previous else None,
        "delivery_id": "F4-P02-" + delivery,
        "media_type": "application/xml",
    }


def run(engine):
    seed(engine)
    before = snapshot(engine)
    expected = json.loads((FIXTURES / "expected.json").read_text())
    reports = []
    # On replay, A2/B2 may already be current. Evaluate the historical versions
    # again, but assert transition-specific regularity only on the first run.
    with engine.connect() as c:
        replay = sql(
            c,
            "SELECT EXISTS(SELECT 1 FROM ilc.document_versions WHERE source_system=:source AND document_id='F4-P02-A2')",
            source=SOURCE,
        ).scalar_one()
    for name in (
        "A1",
        "B1",
        "MISSING",
        "REFERENCE",
        "TIME",
        "UNIT",
        "UNCONFIRMED",
        "CONTESTED",
        "B2",
        "A2",
    ):
        family = "A" if name.startswith("A") else "B" if name.startswith("B") else None
        previous = name[0] + "1" if name in ("A2", "B2") else None
        env = envelope(
            name,
            delivery=name
            if name
            in ("UNCONFIRMED", "CONTESTED", "MISSING", "REFERENCE", "TIME", "UNIT")
            else "AB",
            family=family,
            version=2 if previous else 1,
            previous=previous,
        )
        extraction = extract_document(engine, FIXTURES / (name + ".xml"), env)
        assert "document_key" in extraction, extraction
        if name in ("B2", "A2") and not replay:
            state = regularity(engine, "F4-P02-AB")
            assert not state["regular"]  # New version has no inherited approval.
            with engine.connect() as c:
                old = sql(
                    c,
                    "SELECT valid_to FROM ilc.document_validities WHERE document_key=(SELECT document_key FROM ilc.document_versions WHERE source_system=:source AND document_id=:id)",
                    source=SOURCE,
                    id="F4-P02-" + previous,
                ).scalar_one()
                assert old is not None
        evaluation = evaluate(engine, extraction["document_key"])
        if expected[name] == "APPROVED":
            assert evaluation["result"] == "APPROVED", evaluation
        else:
            assert evaluation["result"] == "REVIEW_REQUIRED"
            assert expected[name] in {r["code"] for r in evaluation["reasons"]}
        repeat = extract_document(engine, FIXTURES / (name + ".xml"), env)
        assert (
            repeat["duplicate"] and repeat["document_key"] == extraction["document_key"]
        )
        # New extraction invalidates the previous evaluation's currency.
        assert not regularity(engine, env["delivery_id"])["regular"]
        reevaluation = evaluate(engine, repeat["document_key"])
        assert reevaluation["number"] == evaluation["number"] + 1
        state_after = regularity(engine, env["delivery_id"])
        if not replay and name in ("A1", "B1", "B2", "A2"):
            assert state_after["regular"] is (name in ("A1", "B2")), state_after
        reports.append(
            {
                "name": name,
                "extraction": repeat,
                "evaluation": reevaluation,
                "regularity": state_after,
            }
        )
    # A/B fixture uses a separate delivery, so unrelated negative fixtures cannot
    # conceal the decisive two-document regularity assertions.
    invalid = extract_document(
        engine, FIXTURES / "A1.xml", envelope("INVALID", delivery="UNKNOWN")
    )
    assert invalid["error_category"] == "INVALID_REFERENCE"
    invalid_chain = extract_document(
        engine,
        FIXTURES / "B2.xml",
        envelope("B4", family="B", version=4, previous="B2"),
    )
    assert invalid_chain["error_category"] == "INVALID_VERSION_CHAIN"
    state = regularity(engine, "F4-P02-AB")
    assert not state["regular"] and state["physical_state"] == "DELIVERED"
    assert regularity(engine, "F4-P02-CONTESTED")["completion_contested"]
    assert before == snapshot(engine)
    with engine.connect() as c:
        overlaps = sql(
            c,
            """SELECT count(*) FROM ilc.document_validities a JOIN ilc.document_validities b
            ON a.family_key=b.family_key AND a.document_key<>b.document_key
            AND tstzrange(a.valid_from,a.valid_to,'[)') && tstzrange(b.valid_from,b.valid_to,'[)')""",
        ).scalar_one()
        assert overlaps == 0
        versions = sql(
            c,
            "SELECT count(*) FROM ilc.document_versions WHERE source_system=:source",
            source=SOURCE,
        ).scalar_one()
        assert versions == 10
    return {
        "verification": "PASS",
        "reports": reports,
        "versions": versions,
        "invalid_reference": invalid,
        "invalid_chain": invalid_chain,
        "overlaps": overlaps,
        "physical_and_p01_preserved": True,
        "regularity": state,
        "replay": replay,
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

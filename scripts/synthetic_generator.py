"""Deterministic input files only: no database, ingestion or document parsing."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
BASE_TIME = datetime(2026, 10, 16, tzinfo=UTC)
STREAMS = (
    "reference/orders.jsonl",
    "reference/deliveries.jsonl",
    "valid/events.jsonl",
    "valid/document_envelopes.jsonl",
    "replays/events.jsonl",
    "replays/document_envelopes.jsonl",
    "anomalies/events.jsonl",
    "anomalies/document_envelopes.jsonl",
    "invalid/events.jsonl",
    "invalid/document_envelopes.jsonl",
    "arrival_plan.jsonl",
    "document_references.jsonl",
)


def json_bytes(value):
    """UTF-8, sorted keys, LF; no platform newline conversion."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def moment(minutes):
    return (
        (BASE_TIME + timedelta(minutes=minutes))
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def divergent_quantity(expected):
    """Cria divergencia sintetica de uma unidade sem quantidade negativa."""
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 1:
        raise ValueError("Expected quantity must be a positive integer")
    return expected - 1


@dataclass(frozen=True)
class Config:
    seed: int = 20261019
    volume: int = 0

    def validate(self):
        if type(self.seed) is not int or not 0 <= self.seed <= 2**63 - 1:
            raise ValueError("Seed must be an integer between zero and 2**63-1")
        if type(self.volume) is not int or not 0 <= self.volume <= 10000:
            raise ValueError(
                "Volume means zero to 10000 additional consistent deliveries"
            )


class Builder:
    def __init__(self, config):
        config.validate()
        self.config = config
        self.rows = {path: [] for path in STREAMS}
        self.assets = {}
        self.cases = []

    def append(self, path, row):
        self.rows[path].append(row)
        return {"path": path, "line": len(self.rows[path])}

    def arrival(self, pointer, case, minutes, classification):
        sequence = len(self.rows["arrival_plan.jsonl"]) + 1
        self.append(
            "arrival_plan.jsonl",
            {
                "arrival_id": f"ARR-{sequence:06d}",
                "sequence": sequence,
                "case_id": case,
                "received_at": moment(minutes),
                "classification": classification,
                "payload": pointer,
            },
        )

    def reference(self, delivery, quantity=10):
        order = "ORD-" + delivery
        self.append(
            "reference/orders.jsonl",
            {
                "source_system": "synthetic_reference",
                "order_id": order,
                "released_at": moment(600),
                "request_data": {"synthetic": True},
            },
        )
        self.append(
            "reference/deliveries.jsonl",
            {
                "order_source_system": "synthetic_reference",
                "order_id": order,
                "delivery_id": delivery,
                "promised_at": moment(1080),
                "expected_quantity": quantity,
                "quantity_unit": "VOLUME",
            },
        )

    def event(
        self,
        case,
        delivery,
        event_id,
        kind="DELIVERED",
        occurred=1020,
        received=None,
        bucket="valid",
        payload=None,
    ):
        if payload is None:
            payload = {
                "schema_version": "1.0",
                "source_system": "synthetic_events",
                "event_id": event_id,
                "delivery_id": delivery,
                "event_type": kind,
                "occurred_at": moment(occurred),
                "notes": f"Synthetic only; seed={self.config.seed}",
            }
        pointer = self.append(bucket + "/events.jsonl", payload)
        self.arrival(pointer, case, occurred if received is None else received, bucket)
        return payload

    def document(
        self,
        case,
        delivery,
        document_id,
        family,
        quantity=10,
        version=1,
        previous=None,
        received=1030,
        bucket="valid",
        variant="original",
    ):
        envelope = {
            "schema_version": "1.0",
            "source_system": "synthetic_documents",
            "document_id": document_id,
            "document_family_id": family,
            "version": version,
            "supersedes_document_id": previous,
            "delivery_id": delivery,
            "media_type": "application/pdf",
        }
        pointer = self.append(bucket + "/document_envelopes.jsonl", envelope)
        asset_path = f"synthetic_documents/{document_id}-{variant}.synthetic.json"
        asset = json_bytes(
            {
                "artifact_type": "SYNTHETIC_DOCUMENT_REFERENCE",
                "is_real_pdf_or_xml": False,
                "seed": self.config.seed,
                "document_id": document_id,
                "intended_media_type": envelope["media_type"],
                "declared_fields_for_future_fixture": {
                    "declared_delivery_id": delivery,
                    "delivered_at": moment(1020),
                    "received_quantity": quantity,
                    "quantity_unit": "VOLUME",
                    "receiver_name": f"Synthetic receiver {self.config.seed}",
                },
            }
        )
        if asset_path in self.assets:
            raise ValueError("Synthetic asset name collision")
        self.assets[asset_path] = asset
        self.append(
            "document_references.jsonl",
            {
                "envelope": pointer,
                "path": asset_path,
                "sha256": sha256(asset),
                "bytes": len(asset),
                "classification": bucket,
            },
        )
        self.arrival(pointer, case, received, bucket)
        return envelope, asset_path

    def replay_document(self, case, envelope, asset_path, received):
        pointer = self.append("replays/document_envelopes.jsonl", dict(envelope))
        asset = self.assets[asset_path]
        self.append(
            "document_references.jsonl",
            {
                "envelope": pointer,
                "path": asset_path,
                "sha256": sha256(asset),
                "bytes": len(asset),
                "classification": "replays",
            },
        )
        self.arrival(pointer, case, received, "replays")

    def expected(self, case, deliveries, assertions):
        self.cases.append(
            {
                "case_id": case,
                "delivery_ids": deliveries,
                "status": "EXPECTED_NOT_EXECUTED",
                "assertions": assertions,
            }
        )

    def fixtures(self):
        # A and B retain the concrete IDs/times/quantities from contracts 06/07.
        self.reference("ENT-001")
        for event_id, kind, time in (
            ("EVT-001", "DISPATCHED", 720),
            ("EVT-002", "IN_TRANSIT", 840),
            ("EVT-003", "DELIVERED", 1020),
        ):
            self.event("A", "ENT-001", event_id, kind, time)
        self.document("A", "ENT-001", "DOC-A1", "POD-A")
        self.document("A", "ENT-001", "DOC-B1", "POD-B", divergent_quantity(10))
        self.expected(
            "A",
            ["ENT-001"],
            [
                "One delivery, three events and two independent document families",
                "DOC-A1 should approve after future consistent extraction/checking",
                "DOC-B1 should require review for VALUE_MISMATCH; no masking by DOC-A1",
            ],
        )

        self.reference("ENT-002")
        self.event("B", "ENT-002", "EVT-B-DELIVERED")
        self.document("B", "ENT-002", "DOC-C1", "POD-C", divergent_quantity(10))
        updated, asset = self.document(
            "B",
            "ENT-002",
            "DOC-C2",
            "POD-C",
            version=2,
            previous="DOC-C1",
            received=1050,
        )
        self.replay_document("B", updated, asset, 1060)
        self.expected(
            "B",
            ["ENT-002"],
            [
                "DOC-C2 supersedes DOC-C1 structurally; no inherited approval",
                "DOC-C1 and its future evaluation remain historical",
                "Identical DOC-C2 replay preserves original reception at 17:30Z",
                "First structurally valid reception remains DOC-C1 at 17:10Z",
            ],
        )

        for suffix, delivery, order in (
            ("AB", "ENT-003", ("A", "B")),
            ("BA", "ENT-004", ("B", "A")),
        ):
            case = "C_" + suffix
            self.reference(delivery)
            for position, alternative in enumerate(order):
                self.event(
                    case,
                    delivery,
                    f"EVT-C-{suffix}-{alternative}",
                    occurred=1020 if alternative == "A" else 1030,
                    received=1040 + position,
                )
            self.expected(
                case,
                [delivery],
                [
                    "One delivery, two preserved DELIVERED alternatives and an open completion conflict",
                    f"First planned acceptance is {order[0]}; provisional time depends on acceptance order",
                    "No automatic choice by occurred_at and no new time-dependent document approval",
                ],
            )

        self.reference("ENT-005")
        original = self.event("CONSISTENT", "ENT-005", "EVT-CONSISTENT")
        self.document("CONSISTENT", "ENT-005", "DOC-CONSISTENT", "POD-CONSISTENT")
        self.event(
            "CONSISTENT",
            "ENT-005",
            "EVT-CONSISTENT",
            received=1040,
            bucket="replays",
            payload=dict(original),
        )
        self.expected(
            "CONSISTENT",
            ["ENT-005"],
            [
                "Consistent synthetic declared fields should approve in the future pipeline",
                "Identical event replay should not create another business event",
            ],
        )

        self.reference("ENT-006")
        self.event("NO_DOCUMENT", "ENT-006", "EVT-NO-DOCUMENT")
        self.expected(
            "NO_DOCUMENT",
            ["ENT-006"],
            [
                "Physically completed but no document input; no fabricated document row",
            ],
        )

        self.reference("ENT-007")
        original = self.event("IDENTITY_CONFLICT", "ENT-007", "EVT-IDENTITY")
        altered = dict(original, occurred_at=moment(1030))
        self.event(
            "IDENTITY_CONFLICT",
            "ENT-007",
            "EVT-IDENTITY",
            received=1040,
            bucket="anomalies",
            payload=altered,
        )
        self.document("IDENTITY_CONFLICT", "ENT-007", "DOC-IDENTITY", "POD-IDENTITY")
        self.document(
            "IDENTITY_CONFLICT",
            "ENT-007",
            "DOC-IDENTITY",
            "POD-IDENTITY",
            divergent_quantity(10),
            received=1050,
            bucket="anomalies",
            variant="alternative",
        )
        self.expected(
            "IDENTITY_CONFLICT",
            ["ENT-007"],
            [
                "Same event identity with changed occurrence is conflict, not an accepted duplicate",
                "Same document identity with different synthetic reference bytes is conflict",
                "Preserve original and alternative; do not overwrite accepted content",
            ],
        )

        self.reference("ENT-008")
        self.event("LATE_EVENT", "ENT-008", "EVT-LATE-DELIVERED")
        self.event("LATE_EVENT", "ENT-008", "EVT-LATE-TRANSIT", "IN_TRANSIT", 840, 1040)
        self.expected(
            "LATE_EVENT",
            ["ENT-008"],
            [
                "Earlier IN_TRANSIT received after DELIVERED enters history without physical regression",
            ],
        )
        self.invalid_cases()

    def invalid_cases(self):
        template = dict(self.rows["valid/events.jsonl"][0])
        wrong_type = dict(template, event_id="INVALID-TYPE", event_type="FINISHED")
        naive_time = dict(
            template, event_id="INVALID-TIME", occurred_at="2026-10-16T12:00:00"
        )
        missing = dict(template, event_id="INVALID-MISSING")
        del missing["delivery_id"]
        for case, payload in (
            ("INVALID_EVENT_TYPE", wrong_type),
            ("INVALID_NAIVE_TIME", naive_time),
            ("INVALID_MISSING_DELIVERY", missing),
        ):
            self.event(
                case,
                "ENT-001",
                payload["event_id"],
                bucket="invalid",
                received=1100,
                payload=payload,
            )
            self.expected(
                case,
                [],
                ["Structurally invalid event should be rejected before acceptance"],
            )
        template = dict(self.rows["valid/document_envelopes.jsonl"][0])
        missing = dict(template, document_id="INVALID-DOC-MISSING")
        del missing["media_type"]
        wrong_chain = dict(
            template,
            document_id="INVALID-DOC-CHAIN",
            version=2,
            supersedes_document_id=None,
        )
        for case, payload in (
            ("INVALID_DOCUMENT_MEDIA", missing),
            ("INVALID_DOCUMENT_PREDECESSOR", wrong_chain),
        ):
            pointer = self.append("invalid/document_envelopes.jsonl", payload)
            self.arrival(pointer, case, 1100, "invalid")
            self.expected(
                case,
                [],
                ["Invalid envelope should not replace a valid document version"],
            )

    def bulk(self):
        for number in range(1, self.config.volume + 1):
            token = sha256(f"{self.config.seed}/bulk/{number}".encode("ascii"))
            quantity = 10 + int(token[:8], 16) % 41
            delivery = f"ENT-BULK-{number:05d}"
            self.reference(delivery, quantity)
            self.event("BULK_CONSISTENT", delivery, f"EVT-BULK-{number:05d}")
            self.document(
                "BULK_CONSISTENT",
                delivery,
                f"DOC-BULK-{number:05d}",
                f"POD-BULK-{number:05d}",
                quantity,
            )
        if self.config.volume:
            self.expected(
                "BULK_CONSISTENT",
                [],
                [
                    "Each additional delivery has one coherent event and one synthetic document reference",
                ],
            )

    def build(self):
        self.fixtures()
        self.bulk()
        # Arrival order is explicit and stable, independent of dictionary/hash seed.
        arrivals = self.rows["arrival_plan.jsonl"]
        arrivals.sort(key=lambda row: (row["received_at"], row["sequence"]))
        for number, arrival in enumerate(arrivals, 1):
            arrival["sequence"] = number
            arrival["arrival_id"] = f"ARR-{number:06d}"
        files = dict(self.assets)
        for path, rows in self.rows.items():
            files[path] = b"".join(json_bytes(row) for row in rows)
        manifest = {
            "generator_version": VERSION,
            "configuration": {
                "seed": self.config.seed,
                "additional_consistent_deliveries": self.config.volume,
                "base_time_utc": moment(0),
                "divergence_rule": "positive-reference-minus-one-v1",
            },
            "execution_scope": "INPUT_GENERATION_ONLY_NO_BUSINESS_RESULTS_EXECUTED",
            "synthetic_only": True,
            "base_fixture_deliveries": 8,
            "counts": {path: len(rows) for path, rows in sorted(self.rows.items())},
            "unique_valid_event_identities": len(
                {
                    (r["source_system"], r["event_id"])
                    for r in self.rows["valid/events.jsonl"]
                }
            ),
            "unique_valid_document_identities": len(
                {
                    (r["source_system"], r["document_id"])
                    for r in self.rows["valid/document_envelopes.jsonl"]
                }
            ),
            "arrivals_by_classification": dict(
                sorted(Counter(r["classification"] for r in arrivals).items())
            ),
            "document_artifact_notice": "JSON references only, not real PDF/XML. Envelope media_type describes the intended future document. No extracted result or file_sha256 of a real document is claimed.",
            "reference_contract_notice": "Order/delivery input layout is an educational adapter derived from model 07, not an approved external API contract.",
            "expected_cases": self.cases,
            "files": {
                path: {"sha256": sha256(content), "bytes": len(content)}
                for path, content in sorted(files.items())
            },
        }
        files["manifest.json"] = json_bytes(manifest)
        files["SHA256SUMS"] = "".join(
            f"{sha256(content)}  {path}\n" for path, content in sorted(files.items())
        ).encode("utf-8")
        return files


def generate(config):
    return Builder(config).build()


def write_dataset(output, files):
    """Create a new destination; never merge into or overwrite an existing directory."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for path, content in sorted(files.items()):
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument(
        "--volume",
        type=int,
        default=0,
        help="Additional consistent deliveries, 0..10000",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="New directory under data/generated/"
    )
    args = parser.parse_args()
    allowed = ROOT / "data" / "generated"
    output = args.output.resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise ValueError("Choose a new child directory under repository data/generated")
    files = generate(Config(args.seed, args.volume))
    write_dataset(output, files)
    manifest = json.loads(files["manifest.json"])
    print("Input generation: PASS")
    print("Seed:", args.seed, "Additional deliveries:", args.volume)
    print("Reference deliveries:", manifest["counts"]["reference/deliveries.jsonl"])
    print("Files:", len(files))
    print("SHA256SUMS SHA256:", sha256(files["SHA256SUMS"]))
    print("Business outcomes: EXPECTED ONLY; no database or parser executed")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, NotImplementedError) as error:
        print(f"Input generation: FAIL ({type(error).__name__})")
        sys.exit(1)

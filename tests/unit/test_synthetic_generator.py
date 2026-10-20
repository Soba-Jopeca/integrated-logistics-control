"""Generator verification only; expected business outcomes are not executed here."""

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from scripts.check_synthetic_dataset import inspect_dataset
from scripts.synthetic_generator import (
    Config,
    divergent_quantity,
    generate,
    write_dataset,
)


def rows(files, path):
    return [json.loads(line) for line in files[path].splitlines()]


class SyntheticGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = generate(Config())
        cls.manifest = json.loads(cls.files["manifest.json"])

    def test_identical_configuration_means_identical_bytes(self):
        self.assertEqual(self.files, generate(Config()))

    def test_clock_random_uuid_and_process_environment_do_not_change_bytes(self):
        with (
            patch("time.time", return_value=0),
            patch("uuid.uuid4", side_effect=AssertionError),
            patch("random.random", side_effect=AssertionError),
            patch.dict(
                os.environ,
                {"DB_PASSWORD": "unused-synthetic-test", "TZ": "Pacific/Honolulu"},
            ),
        ):
            self.assertEqual(self.files, generate(Config()))

    def test_different_seed_changes_payload_content(self):
        changed = generate(Config(seed=7))
        self.assertNotEqual(
            self.files["valid/events.jsonl"], changed["valid/events.jsonl"]
        )
        self.assertNotEqual(
            self.files["synthetic_documents/DOC-A1-original.synthetic.json"],
            changed["synthetic_documents/DOC-A1-original.synthetic.json"],
        )

    def test_volume_adds_coherent_deliveries_without_replacing_fixtures(self):
        expanded = generate(Config(volume=3))
        summary = json.loads(expanded["manifest.json"])
        self.assertEqual(summary["counts"]["reference/deliveries.jsonl"], 11)
        self.assertEqual(summary["counts"]["valid/events.jsonl"], 16)
        self.assertEqual(summary["counts"]["valid/document_envelopes.jsonl"], 9)
        for path in (
            "valid/events.jsonl",
            "valid/document_envelopes.jsonl",
            "reference/deliveries.jsonl",
        ):
            self.assertTrue(expanded[path].startswith(self.files[path]))
        deliveries = {
            r["delivery_id"]: r for r in rows(expanded, "reference/deliveries.jsonl")
        }
        for envelope in rows(expanded, "valid/document_envelopes.jsonl"):
            if envelope["delivery_id"].startswith("ENT-BULK-"):
                asset = json.loads(
                    expanded[
                        f"synthetic_documents/{envelope['document_id']}-original.synthetic.json"
                    ]
                )
                self.assertEqual(
                    asset["declared_fields_for_future_fixture"]["received_quantity"],
                    deliveries[envelope["delivery_id"]]["expected_quantity"],
                )

    def test_small_fixture_counts_are_explicit(self):
        expected = {
            "reference/orders.jsonl": 8,
            "reference/deliveries.jsonl": 8,
            "valid/events.jsonl": 13,
            "valid/document_envelopes.jsonl": 6,
            "replays/events.jsonl": 1,
            "replays/document_envelopes.jsonl": 1,
            "anomalies/events.jsonl": 1,
            "anomalies/document_envelopes.jsonl": 1,
            "invalid/events.jsonl": 3,
            "invalid/document_envelopes.jsonl": 2,
            "arrival_plan.jsonl": 28,
            "document_references.jsonl": 8,
        }
        self.assertEqual(self.manifest["counts"], expected)
        self.assertEqual(len(self.files), 21)

    def test_all_valid_event_links_and_contract_fields(self):
        deliveries = {
            r["delivery_id"] for r in rows(self.files, "reference/deliveries.jsonl")
        }
        events = rows(self.files, "valid/events.jsonl")
        self.assertEqual(len({(r["source_system"], r["event_id"]) for r in events}), 13)
        for event in events:
            self.assertEqual(
                set(event),
                {
                    "schema_version",
                    "source_system",
                    "event_id",
                    "delivery_id",
                    "event_type",
                    "occurred_at",
                    "notes",
                },
            )
            self.assertIn(event["delivery_id"], deliveries)
            self.assertIn(
                event["event_type"], {"DISPATCHED", "IN_TRANSIT", "DELIVERED"}
            )
            self.assertEqual(event["schema_version"], "1.0")
            self.assertIsNotNone(datetime.fromisoformat(event["occurred_at"]).tzinfo)

    def test_order_delivery_references_are_unique_and_coherent(self):
        orders = rows(self.files, "reference/orders.jsonl")
        keys = {(r["source_system"], r["order_id"]) for r in orders}
        deliveries = rows(self.files, "reference/deliveries.jsonl")
        self.assertEqual(len(keys), 8)
        self.assertEqual(len({r["delivery_id"] for r in deliveries}), 8)
        for delivery in deliveries:
            self.assertIn((delivery["order_source_system"], delivery["order_id"]), keys)
            self.assertGreaterEqual(delivery["expected_quantity"], 0)

    def test_document_version_chains_remain_in_same_family_and_delivery(self):
        envelopes = rows(self.files, "valid/document_envelopes.jsonl")
        by_id = {(r["source_system"], r["document_id"]): r for r in envelopes}
        deliveries = {
            r["delivery_id"] for r in rows(self.files, "reference/deliveries.jsonl")
        }
        self.assertEqual(len(by_id), 6)
        for envelope in envelopes:
            self.assertEqual(
                set(envelope),
                {
                    "schema_version",
                    "source_system",
                    "document_id",
                    "document_family_id",
                    "version",
                    "supersedes_document_id",
                    "delivery_id",
                    "media_type",
                },
            )
            self.assertIn(envelope["delivery_id"], deliveries)
            if envelope["version"] == 1:
                self.assertIsNone(envelope["supersedes_document_id"])
            else:
                previous = by_id[
                    (envelope["source_system"], envelope["supersedes_document_id"])
                ]
                self.assertEqual(previous["version"] + 1, envelope["version"])
                for field in ("document_family_id", "delivery_id", "source_system"):
                    self.assertEqual(previous[field], envelope[field])

    def test_A_and_B_match_approved_quantities_and_versions(self):
        declared = {
            path: json.loads(content)["declared_fields_for_future_fixture"]
            for path, content in self.files.items()
            if path.startswith("synthetic_documents/")
        }
        for doc, quantity in (
            ("DOC-A1", 10),
            ("DOC-B1", 9),
            ("DOC-C1", 9),
            ("DOC-C2", 10),
        ):
            self.assertEqual(
                declared[f"synthetic_documents/{doc}-original.synthetic.json"][
                    "received_quantity"
                ],
                quantity,
            )
        self.assertEqual(
            len(
                [
                    r
                    for r in rows(self.files, "valid/events.jsonl")
                    if r["delivery_id"] == "ENT-001"
                ]
            ),
            3,
        )

    def test_document_references_have_real_hashes_of_synthetic_bytes_only(self):
        for reference in rows(self.files, "document_references.jsonl"):
            content = self.files[reference["path"]]
            self.assertEqual(reference["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(reference["bytes"], len(content))
            self.assertFalse(json.loads(content)["is_real_pdf_or_xml"])
            self.assertTrue(reference["path"].endswith(".synthetic.json"))
        self.assertFalse(any(path.endswith((".pdf", ".xml")) for path in self.files))

    def test_identical_replays_and_changed_identity_alternatives(self):
        events = {
            (r["source_system"], r["event_id"]): r
            for r in rows(self.files, "valid/events.jsonl")
        }
        replay = rows(self.files, "replays/events.jsonl")[0]
        self.assertEqual(replay, events[(replay["source_system"], replay["event_id"])])
        alternative = rows(self.files, "anomalies/events.jsonl")[0]
        self.assertNotEqual(
            alternative, events[(alternative["source_system"], alternative["event_id"])]
        )
        envelopes = {
            r["document_id"]: r
            for r in rows(self.files, "valid/document_envelopes.jsonl")
        }
        self.assertEqual(
            rows(self.files, "replays/document_envelopes.jsonl")[0], envelopes["DOC-C2"]
        )
        self.assertEqual(
            rows(self.files, "anomalies/document_envelopes.jsonl")[0],
            envelopes["DOC-IDENTITY"],
        )
        original = self.files[
            "synthetic_documents/DOC-IDENTITY-original.synthetic.json"
        ]
        changed = self.files[
            "synthetic_documents/DOC-IDENTITY-alternative.synthetic.json"
        ]
        self.assertNotEqual(original, changed)

    def test_arrival_plan_preserves_reception_semantics(self):
        arrivals = rows(self.files, "arrival_plan.jsonl")
        self.assertEqual([r["sequence"] for r in arrivals], list(range(1, 29)))
        self.assertEqual(len({r["arrival_id"] for r in arrivals}), 28)
        times = [r["received_at"] for r in arrivals]
        self.assertEqual(times, sorted(times))
        for arrival in arrivals:
            pointer = arrival["payload"]
            self.assertGreaterEqual(pointer["line"], 1)
            self.assertLessEqual(
                pointer["line"], len(rows(self.files, pointer["path"]))
            )
        for case, first in (("C_AB", "A"), ("C_BA", "B")):
            selected = [r for r in arrivals if r["case_id"] == case]
            pointer = selected[0]["payload"]
            event = rows(self.files, pointer["path"])[pointer["line"] - 1]
            self.assertTrue(event["event_id"].endswith("-" + first))
        b = [
            r
            for r in arrivals
            if r["case_id"] == "B"
            and r["payload"]["path"].endswith("document_envelopes.jsonl")
        ]
        self.assertEqual(
            [r["received_at"] for r in b],
            ["2026-10-16T17:10:00Z", "2026-10-16T17:30:00Z", "2026-10-16T17:40:00Z"],
        )

    def test_late_event_and_absence_are_deliberate(self):
        events = rows(self.files, "valid/events.jsonl")
        late = {r["event_id"]: r for r in events if r["delivery_id"] == "ENT-008"}
        self.assertLess(
            late["EVT-LATE-TRANSIT"]["occurred_at"],
            late["EVT-LATE-DELIVERED"]["occurred_at"],
        )
        arrivals = [
            r
            for r in rows(self.files, "arrival_plan.jsonl")
            if r["case_id"] == "LATE_EVENT"
        ]
        self.assertLess(arrivals[0]["received_at"], arrivals[1]["received_at"])
        self.assertFalse(
            any(
                r["delivery_id"] == "ENT-006"
                for r in rows(self.files, "valid/document_envelopes.jsonl")
            )
        )

    def test_invalid_inputs_are_isolated_and_have_expected_labels(self):
        events = rows(self.files, "invalid/events.jsonl")
        self.assertEqual(events[0]["event_type"], "FINISHED")
        self.assertIsNone(datetime.fromisoformat(events[1]["occurred_at"]).tzinfo)
        self.assertNotIn("delivery_id", events[2])
        documents = rows(self.files, "invalid/document_envelopes.jsonl")
        self.assertNotIn("media_type", documents[0])
        self.assertEqual(documents[1]["version"], 2)
        self.assertIsNone(documents[1]["supersedes_document_id"])
        labels = {r["case_id"] for r in self.manifest["expected_cases"]}
        for arrival in rows(self.files, "arrival_plan.jsonl"):
            self.assertIn(arrival["case_id"], labels)
            self.assertTrue(
                arrival["payload"]["path"].startswith(arrival["classification"] + "/")
            )

    def test_manifest_and_checksum_inventory_match_actual_bytes(self):
        listed = self.manifest["files"]
        self.assertEqual(set(listed), set(self.files) - {"manifest.json", "SHA256SUMS"})
        for path, metadata in listed.items():
            self.assertEqual(
                metadata["sha256"], hashlib.sha256(self.files[path]).hexdigest()
            )
            self.assertEqual(metadata["bytes"], len(self.files[path]))
        checks = {
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in self.files["SHA256SUMS"].decode().splitlines()
        }
        self.assertEqual(set(checks), set(self.files) - {"SHA256SUMS"})
        for path, digest in checks.items():
            self.assertEqual(digest, hashlib.sha256(self.files[path]).hexdigest())

    def test_expected_business_outcomes_are_not_reported_as_observed(self):
        self.assertEqual(
            self.manifest["execution_scope"],
            "INPUT_GENERATION_ONLY_NO_BUSINESS_RESULTS_EXECUTED",
        )
        self.assertTrue(
            all(
                case["status"] == "EXPECTED_NOT_EXECUTED"
                for case in self.manifest["expected_cases"]
            )
        )

    def test_bytes_are_utf8_lf_and_independent_of_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            write_dataset(first, self.files)
            write_dataset(second, generate(Config()))
            for path, expected in self.files.items():
                self.assertEqual((first / path).read_bytes(), expected)
                self.assertEqual((second / path).read_bytes(), expected)
                self.assertNotIn(b"\r", expected)
                expected.decode("utf-8")

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing"
            output.mkdir()
            protected = output / "keep.txt"
            protected.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                write_dataset(output, self.files)
            self.assertEqual(protected.read_bytes(), b"keep")
            self.assertEqual(list(output.iterdir()), [protected])

    def test_verifier_detects_changed_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dataset"
            write_dataset(output, self.files)
            self.assertEqual(inspect_dataset(output)[0], self.files)
            target = output / "valid/events.jsonl"
            target.write_bytes(b"changed\n")
            with self.assertRaises(ValueError):
                inspect_dataset(output)
            target.write_bytes(self.files["valid/events.jsonl"])
            extra = output / "extra.txt"
            extra.write_bytes(b"unexpected")
            with self.assertRaises(ValueError):
                inspect_dataset(output)
            extra.unlink()
            target.unlink()
            with self.assertRaises(ValueError):
                inspect_dataset(output)

    def test_versioned_small_fixture_matches_current_generation(self):
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic" / "v1"
        self.assertEqual(inspect_dataset(fixture)[0], self.files)

    def test_configuration_boundaries_and_practice_rule(self):
        for config in (
            Config(seed=-1),
            Config(seed=True),
            Config(seed=2**63),
            Config(volume=-1),
            Config(volume=True),
            Config(volume=10001),
        ):
            with self.subTest(config=config), self.assertRaises(ValueError):
                config.validate()
        self.assertEqual(divergent_quantity(10), 9)
        self.assertEqual(divergent_quantity(1), 0)
        for value in (0, -1, True, 1.5, "10"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                divergent_quantity(value)

    def test_no_external_or_database_imports(self):
        import scripts.synthetic_generator as generator

        tree = ast.parse(Path(generator.__file__).read_text(encoding="utf-8"))
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(
                    node.func.attr, {"now", "today", "utcnow", "uuid4", "urandom"}
                )
        self.assertLessEqual(
            modules,
            {
                "argparse",
                "hashlib",
                "json",
                "sys",
                "collections",
                "dataclasses",
                "datetime",
                "pathlib",
            },
        )

    def test_separate_processes_ignore_pythonhashseed(self):
        command = [
            sys.executable,
            "-c",
            "from scripts.synthetic_generator import Config,generate,sha256; print(sha256(generate(Config())['SHA256SUMS']))",
        ]
        root = Path(__file__).resolve().parents[2]
        outputs = []
        for seed in ("1", "12345"):
            result = subprocess.run(
                command,
                cwd=root,
                env={**os.environ, "PYTHONHASHSEED": seed},
                capture_output=True,
                text=True,
                check=True,
            )
            outputs.append(result.stdout.strip())
        self.assertEqual(outputs[0], outputs[1])

    def test_cli_rejects_destination_outside_generated_directory(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "outside"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.synthetic_generator",
                    "--output",
                    str(output),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

"""Offline evaluation harness: loopback only, no database imports/writes."""

import argparse
import hashlib
import json
import platform
import socket
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4
from xml.sax.saxutils import escape

from src.documents.parser import FIELDS, DocumentError, normalize_delivered_at, parse

ROOT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"
DIGEST = "65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b"
OPTIONS = {
    "temperature": 0,
    "seed": 42,
    "num_ctx": 2048,
    "num_predict": 256,
    "num_thread": 4,
    "num_gpu": 0,
}
MAX_RESPONSE = 1_048_576
TIMEOUT = 60


class ExperimentError(Exception):
    """Categorized infrastructure or response failure."""


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ExperimentError("DUPLICATE_JSON_KEY")
        obj[k] = v
    return obj


def json_value(value):
    try:
        return json.loads(value, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        raise ExperimentError("INVALID_JSON") from None


def validate(data):
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise ExperimentError("INVALID_SCHEMA")
    for field, value in data.items():
        if value is None:
            continue
        if field == "received_quantity":
            if type(value) is not int or not 0 <= value <= 2147483647:
                raise ExperimentError("INVALID_SCHEMA")
        elif type(value) is not str or not value.strip():
            raise ExperimentError("INVALID_SCHEMA")
        elif field == "delivered_at":
            try:
                normalize_delivered_at(value)
            except DocumentError:
                raise ExperimentError("INVALID_SCHEMA") from None
    return data


def baseline(text):
    # Adapter for the exact-label text extracted upstream; same parser as P01.
    values = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in FIELDS:
            key = key.strip()
            if key in values:
                raise DocumentError("DUPLICATE_FIELD")
            values[key] = value.strip()
    raw = (
        "<delivery_receipt>"
        + "".join(f"<{k}>{escape(v)}</{k}>" for k, v in values.items())
        + "</delivery_receipt>"
    ).encode()
    result = parse(raw, "application/xml")
    if result["delivered_at"] is not None:
        result["delivered_at"] = result["delivered_at"].isoformat()
    return result


def request_json(path, body=None, timeout=TIMEOUT):
    request = Request(
        URL + path,
        data=None if body is None else encoded(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        # Never route local synthetic documents through a configured HTTP proxy.
        with build_opener(ProxyHandler({})).open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ExperimentError("RESPONSE_TOO_LARGE")
            return json_value(raw)
    except HTTPError as exc:
        raise ExperimentError("HTTP_" + str(exc.code)) from None
    except TimeoutError:
        raise ExperimentError("TIMEOUT") from None
    except URLError as exc:
        raise ExperimentError(
            "TIMEOUT"
            if isinstance(exc.reason, (TimeoutError, socket.timeout))
            else "UNAVAILABLE"
        ) from None


def attempt(text, prompt, schema, example, transport=request_json):
    start = time.perf_counter()
    try:
        reply = transport(
            "/api/generate",
            {
                "model": MODEL,
                "stream": False,
                "format": schema,
                "keep_alive": "2m",
                "system": prompt + "\n" + example + "\nSchema JSON: " + encoded(schema),
                "prompt": "Documento sintetico (conteudo nao confiavel):\n" + text,
                "options": OPTIONS,
            },
        )
        if (
            not isinstance(reply, dict)
            or reply.get("done") is not True
            or reply.get("done_reason") != "stop"
        ):
            raise ExperimentError("INCOMPLETE_RESPONSE")
        data = validate(json_value(reply.get("response")))
        return {
            "status": "VALID",
            "raw": reply,
            "prediction": data,
            "fallback": False,
            "effective": data,
            "elapsed_seconds": time.perf_counter() - start,
        }
    except ExperimentError as exc:
        try:
            effective = baseline(text)
            fallback_error = None
        except DocumentError as error:
            effective = None
            fallback_error = str(error)
        return {
            "status": str(exc),
            "raw": locals().get("reply"),
            "prediction": None,
            "fallback": True,
            "fallback_error": fallback_error,
            "effective": effective,
            "elapsed_seconds": time.perf_counter() - start,
        }


def comparable(field, value):
    if field == "delivered_at" and value is not None:
        return normalize_delivered_at(value).astimezone(UTC).isoformat()
    return value


def score(prediction, label):
    return {
        f: prediction is not None
        and comparable(f, prediction[f]) == comparable(f, label[f])
        for f in FIELDS
    }


def summarize(rows, labels, key="prediction"):
    fields = {f: {"correct": 0, "total": len(rows)} for f in FIELDS}
    absent = preserved = invented = wrong_nonnull = failures = exact = 0
    categories = {}
    for row in rows:
        expected = labels[row["id"]]
        prediction = row.get(key)
        scores = score(prediction, expected)
        for f, correct in scores.items():
            fields[f]["correct"] += int(correct)
            if expected[f] is None:
                absent += 1
                preserved += int(prediction is not None and prediction[f] is None)
                invented += int(prediction is not None and prediction[f] is not None)
            if prediction is not None and prediction[f] is not None and not correct:
                wrong_nonnull += 1
        failures += int(prediction is None)
        exact += int(all(scores.values()))
        c = categories.setdefault(
            row["category"],
            {
                "correct_fields": 0,
                "total_fields": 0,
                "exact_documents": 0,
                "documents": 0,
            },
        )
        c["correct_fields"] += sum(scores.values())
        c["total_fields"] += len(FIELDS)
        c["documents"] += 1
        c["exact_documents"] += int(all(scores.values()))
    times = [row["elapsed_seconds"] for row in rows]
    return {
        "by_field": fields,
        "by_category": categories,
        "exact_documents": exact,
        "documents": len(rows),
        "absence_slots": absent,
        "absence_preserved": preserved,
        "invented_in_absent_fields": invented,
        "incorrect_nonnull_values": wrong_nonnull,
        "failures": failures,
        "fallbacks": sum(bool(row.get("fallback")) for row in rows),
        "latency_seconds": {
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "sum": sum(times),
        },
    }


def execute(output_root):
    evaluation = json.loads((ROOT / "evaluation.json").read_text(encoding="utf-8"))
    # Labels are used for scoring only, never sent to the model.
    labels = json.loads((ROOT / "labels.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schema.json").read_text())
    prompts = {
        v: (ROOT / "prompts" / f"{v}.txt").read_text(encoding="utf-8")
        for v in ("v1", "v2")
    }
    if "JOAO_EDITAR" in prompts["v2"]:
        raise ExperimentError("AUTHOR_PROMPT_PENDING")
    example = (ROOT / "prompt_example.txt").read_text(encoding="utf-8")
    for label in labels.values():
        validate(label)
    assert {x["id"] for x in evaluation} == set(labels)
    version = request_json("/api/version")
    models = request_json("/api/tags")
    selected = next((m for m in models["models"] if m["name"] == MODEL), None)
    if selected is None or selected["digest"] != DIGEST:
        raise ExperimentError("MODEL_DIGEST_MISMATCH")
    if version.get("version") != "0.40.13":
        raise ExperimentError("RUNTIME_VERSION_MISMATCH")
    run = "ai-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + str(uuid4())
    destination = Path(output_root) / run
    destination.mkdir(parents=True, exist_ok=False)
    files = [
        "evaluation.json",
        "labels.json",
        "schema.json",
        "prompt_example.txt",
        "prompts/v1.txt",
        "prompts/v2.txt",
        "runner.py",
    ]
    report = {
        "run_id": run,
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "runtime": version,
        "model": selected,
        "options": OPTIONS,
        "timeout_seconds": TIMEOUT,
        "keep_alive": "2m",
        "input_hashes": {f: sha((ROOT / f).read_bytes()) for f in files},
        "rows": [],
        "summaries": {},
    }
    for f in files:
        target = destination / "inputs" / f
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / f).read_bytes())
    try:
        for index, case in enumerate(evaluation):
            start = time.perf_counter()
            try:
                prediction = baseline(case["text"])
                error = None
            except DocumentError as exc:
                prediction = None
                error = str(exc)
            report["rows"].append(
                {
                    "method": "baseline",
                    "id": case["id"],
                    "category": case["category"],
                    "prediction": prediction,
                    "status": error or "VALID",
                    "elapsed_seconds": time.perf_counter() - start,
                }
            )
            # Alternate prompt order per case to reduce systematic warm-cache bias.
            order = ("v1", "v2") if index % 2 == 0 else ("v2", "v1")
            for v in order:
                row = attempt(case["text"], prompts[v], schema, example)
                row.update(method=v, id=case["id"], category=case["category"])
                report["rows"].append(row)
                print(
                    f"{case['id']} {v}: {row['status']} fallback={row['fallback']}",
                    flush=True,
                )
                (destination / "partial.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        for method in ("baseline", "v1", "v2"):
            rows = [r for r in report["rows"] if r["method"] == method]
            report["summaries"][method] = summarize(rows, labels)
            if method != "baseline":
                report["summaries"][method + "_with_fallback"] = summarize(
                    rows, labels, key="effective"
                )
        report["finished_at"] = datetime.now(UTC).isoformat()
        (destination / "results.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "run_id": run,
                    "results": str(destination / "results.json"),
                    "summaries": report["summaries"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        try:
            request_json(
                "/api/generate",
                {"model": MODEL, "keep_alive": 0, "stream": False},
                timeout=10,
            )
        except ExperimentError as exc:
            print("UNLOAD_FAILED:" + str(exc))
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output-root", default="data/experiments/local_ai")
    args = p.parse_args()
    try:
        execute(args.output_root)
    except ExperimentError as exc:
        print("EXPERIMENT_STOPPED:" + str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""API -> bytes preservados no PostgreSQL de teste; sem entidades de negocio."""

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from scripts.migration_config import TEST_DATABASE, test_engine

MAX_BODY = 1048576
STAGE = "API_CAPTURE_P02A"


class CaptureError(Exception):
    """Categoria publica sem URL de banco ou detalhes sensiveis."""


def now():
    return datetime.now(UTC)


def endpoint_url(value):
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid local API port") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
        or not port
        or parsed.path != "/events"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Use http://127.0.0.1:PORT/events without query or credentials"
        )
    return value


def validate_page(raw, snapshot, expected_total, cursor, seen, limit, source):
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise CaptureError("INVALID_JSON") from exc
    if not isinstance(data, dict) or set(data) != {
        "items",
        "total",
        "dataset_id",
        "next_cursor",
        "has_more",
    }:
        raise CaptureError("INVALID_ENVELOPE")
    items, total = data["items"], data["total"]
    dataset, following, more = data["dataset_id"], data["next_cursor"], data["has_more"]
    if (
        not isinstance(items, list)
        or len(items) > limit
        or type(total) is not int
        or not 0 <= total <= 10000
        or not isinstance(dataset, str)
        or not re.fullmatch(r"[0-9a-f]{64}", dataset)
        or type(more) is not bool
    ):
        raise CaptureError("INVALID_ENVELOPE")
    if snapshot is not None and (dataset != snapshot or total != expected_total):
        raise CaptureError("SNAPSHOT_CHANGED")
    if more:
        if (
            not isinstance(following, str)
            or not 1 <= len(following) <= 256
            or following == cursor
            or following in seen
            or not items
        ):
            raise CaptureError("INVALID_TERMINATION")
    elif following is not None:
        raise CaptureError("INVALID_TERMINATION")
    for item in items:
        if (
            not isinstance(item, dict)
            or item.get("source_system") != source
            or not isinstance(item.get("event_id"), str)
            or not item["event_id"]
            or item["event_id"] != item["event_id"].strip()
        ):
            raise CaptureError("INVALID_PROVENANCE")
    return data


def write_page(
    connection,
    run_id,
    number,
    source,
    url,
    cursor,
    raw,
    status,
    content_type,
    received,
    data,
    category,
):
    """Uma pagina completa e suas entradas na MESMA transacao do chamador."""
    page_key = uuid4()
    checksum = hashlib.sha256(raw).hexdigest()
    captured = category is None
    items = data["items"] if captured else []
    connection.execute(
        text("""
        INSERT INTO ilc.capture_pages
        (page_key,run_id,page_number,source_system,request_url,requested_cursor,
         received_at,http_status,content_type,response_body,response_sha256,
         capture_status,dataset_id,api_total,next_cursor,item_count)
        VALUES (:key,:run,:number,:source,:url,:cursor,:received,:status,:type,
                :body,:hash,:state,:dataset,:total,:next,:count)
    """),
        {
            "key": page_key,
            "run": run_id,
            "number": number,
            "source": source,
            "url": url,
            "cursor": cursor,
            "received": received,
            "status": status,
            "type": content_type,
            "body": raw,
            "hash": checksum,
            "state": "CAPTURED"
            if captured
            else ("HTTP_ERROR" if category == "HTTP_ERROR" else "INVALID_RESPONSE"),
            "dataset": data["dataset_id"] if captured else None,
            "total": data["total"] if captured else None,
            "next": data["next_cursor"] if captured else None,
            "count": len(items),
        },
    )
    reference = "pg:ilc.capture_pages/" + str(page_key)
    for index, item in enumerate(items):
        input_key, receipt_key, attempt_id = uuid4(), uuid4(), uuid4()
        connection.execute(
            text("""
            INSERT INTO ilc.inputs
            (input_key,source_system,input_type,declared_id,original_reference,
             original_sha256,received_at,normalization_error)
            VALUES (:key,:source,'EVENT',:id,:reference,:hash,:received,
                    'NOT_NORMALIZED_CAPTURE_ONLY_P02A')
        """),
            {
                "key": input_key,
                "source": source,
                "id": item["event_id"],
                "reference": reference,
                "hash": checksum,
                "received": received,
            },
        )
        connection.execute(
            text("""
            INSERT INTO ilc.receipts
            (receipt_key,input_key,attempt_received_at,original_reference,original_sha256)
            VALUES (:receipt,:key,:received,:reference,:hash)
        """),
            {
                "receipt": receipt_key,
                "key": input_key,
                "received": received,
                "reference": reference,
                "hash": checksum,
            },
        )
        connection.execute(
            text("""
            INSERT INTO ilc.attempts
            (attempt_id,input_key,run_id,receipt_key,started_at,ended_at,outcome)
            VALUES (:attempt,:key,:run,:receipt,:received,:ended,'ACCEPTED')
        """),
            {
                "attempt": attempt_id,
                "key": input_key,
                "run": run_id,
                "receipt": receipt_key,
                "received": received,
                "ended": now(),
            },
        )
        connection.execute(
            text("""
            INSERT INTO ilc.capture_items(page_key,item_index,input_key)
            VALUES (:page,:index,:key)
        """),
            {"page": page_key, "index": index, "key": input_key},
        )
    return len(items)


def commit_page(engine, **page):
    """Confirma a pagina recebida em uma unica transacao."""
    with engine.begin() as connection:
        return write_page(connection, **page)


def counts(connection, run_id):
    result = (
        connection.execute(
            text("""
        SELECT count(*) AS responses,
               count(*) FILTER (WHERE capture_status='CAPTURED') AS pages,
               coalesce(sum(item_count),0) AS declared_items
        FROM ilc.capture_pages WHERE run_id=:run
    """),
            {"run": run_id},
        )
        .mappings()
        .one()
    )
    records = connection.execute(
        text("""
        SELECT count(*) FROM ilc.capture_items i
        JOIN ilc.capture_pages p USING (page_key) WHERE p.run_id=:run
    """),
        {"run": run_id},
    ).scalar_one()
    return {**dict(result), "records": records}


def capture(
    engine, url, source="synthetic_events", limit=5, timeout=2.0, fail_http_after=None
):
    url = endpoint_url(url)
    if (
        not 1 <= limit <= 100
        or not 0.1 <= timeout <= 30
        or not source
        or source != source.strip()
        or (fail_http_after is not None and fail_http_after < 0)
    ):
        raise ValueError("Invalid capture configuration")
    run_id = "capture-" + str(uuid4())
    with engine.begin() as connection:
        identity = connection.execute(
            text("SELECT current_database(),current_user")
        ).one()
        revision = connection.execute(
            text("SELECT version_num FROM public.alembic_version")
        ).scalar_one()
        if (
            tuple(identity) != (TEST_DATABASE, "ilc_app")
            or revision != "0004_api_capture"
        ):
            raise CaptureError("WRONG_DATABASE_OR_REVISION")
        connection.execute(
            text("""
            INSERT INTO ilc.sources(source_system,description) VALUES (:source,:description)
            ON CONFLICT (source_system) DO NOTHING
        """),
            {"source": source, "description": "Synthetic API capture P02A"},
        )
        connection.execute(
            text("""
            INSERT INTO ilc.runs(run_id,stage,started_at,status)
            VALUES (:run,:stage,:started,'RUNNING')
        """),
            {"run": run_id, "stage": STAGE, "started": now()},
        )
    category = None
    snapshot = total = cursor = None
    seen = set()
    observed = 0
    try:
        with httpx.Client(
            trust_env=False,
            timeout=timeout,
            follow_redirects=False,
            headers={"Accept-Encoding": "identity"},
        ) as client:
            for number in range(1, 10002):
                request = url
                if fail_http_after is not None and number > fail_http_after:
                    request = url.removesuffix("/events") + "/scenarios/http-503"
                params = {"limit": limit}
                if cursor is not None:
                    params["cursor"] = cursor
                with client.stream("GET", request, params=params) as response:
                    chunks, size = [], 0
                    for chunk in response.iter_raw():
                        size += len(chunk)
                        if size > MAX_BODY:
                            raise CaptureError("RESPONSE_TOO_LARGE")
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                    received = now()
                    data = None
                    problem = None
                    if response.status_code != 200:
                        problem = "HTTP_ERROR"
                    else:
                        try:
                            data = validate_page(
                                raw, snapshot, total, cursor, seen, limit, source
                            )
                        except CaptureError as exc:
                            problem = str(exc)
                    # Cursor so muda DEPOIS que commit_page retorna com commit confirmado.
                    observed += commit_page(
                        engine,
                        run_id=run_id,
                        number=number,
                        source=source,
                        url=str(response.request.url),
                        cursor=cursor,
                        raw=raw,
                        status=response.status_code,
                        content_type=response.headers.get("content-type", ""),
                        received=received,
                        data=data,
                        category=problem,
                    )
                    if problem:
                        raise CaptureError(problem)
                    snapshot, total = data["dataset_id"], data["total"]
                    if not data["has_more"]:
                        if observed != total:
                            raise CaptureError("COUNT_MISMATCH")
                        break
                    seen.add(data["next_cursor"])
                    cursor = data["next_cursor"]
                    if observed >= total:
                        raise CaptureError("COUNT_MISMATCH")
            else:
                raise CaptureError("PAGE_LIMIT")
    except CaptureError as exc:
        category = str(exc)
    except httpx.HTTPError as exc:
        category = type(exc).__name__
    except SQLAlchemyError:
        category = "PERSISTENCE_ERROR"
    with engine.begin() as connection:
        persisted = counts(connection, run_id)
        if (
            persisted["declared_items"] != persisted["records"]
            or persisted["records"] != observed
        ):
            category = category or "PERSISTENCE_COUNT_MISMATCH"
        connection.execute(
            text("""
            UPDATE ilc.runs SET status=:status,ended_at=:ended,error_category=:error
            WHERE run_id=:run
        """),
            {
                "status": "FAILED" if category else "SUCCEEDED",
                "ended": now(),
                "error": category,
                "run": run_id,
            },
        )
    return {
        "run_id": run_id,
        "status": "FAILED" if category else "SUCCEEDED",
        "error_category": category,
        "expected_total": total,
        **persisted,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--url", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=2)
    parser.add_argument("--simulate-http-after-pages", type=int)
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        report = capture(
            engine,
            args.url,
            limit=args.limit,
            timeout=args.timeout,
            fail_http_after=args.simulate_http_after_pages,
        )
        print(json.dumps(report, default=str))
        return 0 if report["status"] == "SUCCEEDED" else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SQLAlchemyError, ValueError, CaptureError, OSError) as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_category": type(exc).__name__,
                    "counts": "UNKNOWN - query database before claiming any commit",
                }
            )
        )
        raise SystemExit(1) from None

"""Restartable loopback capture, atomic checkpoints and bounded transient retries."""

import argparse
import hashlib
import json
import time
from uuid import uuid4

import httpx
from sqlalchemy.exc import SQLAlchemyError

from scripts.api_capture import (
    MAX_BODY,
    CaptureError,
    counts,
    endpoint_url,
    now,
    validate_page,
    write_page,
)
from scripts.business_load import sql
from scripts.migration_config import TEST_DATABASE, test_engine

TRANSIENT_STATUS = frozenset({408, 429, 500, 502, 503, 504})
TRANSIENT_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
BACKOFF = (0.1, 0.2)


def request(client, url, params, audit, timeout=2.0, sleep=time.sleep):
    for attempt in range(1, 4):
        started, body, status, error = now(), None, None, None
        try:
            with client.stream("GET", url, params=params, timeout=timeout) as response:
                status = response.status_code
                pieces, size = [], 0
                for piece in response.iter_raw():
                    size += len(piece)
                    if size > MAX_BODY:
                        raise CaptureError("RESPONSE_TOO_LARGE")
                    pieces.append(piece)
                body = b"".join(pieces)
        except TRANSIENT_ERRORS as exc:
            error = type(exc).__name__
        except (httpx.HTTPError, CaptureError) as exc:
            audit(attempt, status, body, type(exc).__name__, started, now())
            raise
        audit(attempt, status, body, error, started, now())
        transient = error is not None or status in TRANSIENT_STATUS
        if not transient:
            return status, body
        if attempt == 3:
            raise CaptureError("RETRY_EXHAUSTED:" + (error or "HTTP_" + str(status)))
        sleep(BACKOFF[attempt - 1])
    raise AssertionError("Unreachable retry state")


def checkpoint(connection, run_id, lock=False):
    return dict(
        sql(
            connection,
            "SELECT * FROM ilc.capture_checkpoints WHERE capture_run_id=:run"
            + (" FOR UPDATE" if lock else ""),
            run=run_id,
        )
        .mappings()
        .one()
    )


def advance_page(
    connection, run_id, invocation, number, url, cursor, raw, status, received, data
):
    prior = checkpoint(connection, run_id, lock=True)
    if (
        prior["complete"]
        or prior["last_page"] + 1 != number
        or prior["next_cursor"] != cursor
    ):
        raise CaptureError("STALE_CHECKPOINT")
    if prior["dataset_id"] is not None and (
        prior["dataset_id"] != data["dataset_id"] or prior["api_total"] != data["total"]
    ):
        raise CaptureError("SNAPSHOT_CHANGED")
    records = prior["records"] + len(data["items"])
    if (
        records > data["total"]
        or (not data["has_more"] and records != data["total"])
        or (data["has_more"] and records >= data["total"])
    ):
        raise CaptureError("COUNT_MISMATCH")
    write_page(
        connection,
        run_id,
        number,
        prior["source_system"],
        url,
        cursor,
        raw,
        status,
        "application/json",
        received,
        data,
        None,
    )
    sql(
        connection,
        """UPDATE ilc.capture_checkpoints SET last_page=:page,records=:records,
        dataset_id=:snapshot,api_total=:total,next_cursor=:cursor,complete=:complete
        WHERE capture_run_id=:run""",
        page=number,
        records=records,
        snapshot=data["dataset_id"],
        total=data["total"],
        cursor=data["next_cursor"],
        complete=not data["has_more"],
        run=run_id,
    )
    sql(
        connection,
        """INSERT INTO ilc.capture_checkpoint_history
        (capture_run_id,page_number,invocation_run_id,records,dataset_id,next_cursor,complete,recorded_at)
        VALUES (:run,:page,:invocation,:records,:snapshot,:cursor,:complete,:time)""",
        run=run_id,
        page=number,
        invocation=invocation,
        records=records,
        snapshot=data["dataset_id"],
        cursor=data["next_cursor"],
        complete=not data["has_more"],
        time=now(),
    )


def commit_page_and_checkpoint(engine, before_commit=False, **page):
    """Joao conecta a gravacao e o checkpoint a uma unica transacao."""
    raise CaptureError("JOAO_RECOVERY_LINK_PENDING")


def start_job(engine):
    run_id = "capture-p03-" + str(uuid4())
    with engine.begin() as connection:
        identity = tuple(
            sql(connection, "SELECT current_database(),current_user").one()
        )
        revision = sql(
            connection, "SELECT version_num FROM public.alembic_version"
        ).scalar_one()
        if identity != (TEST_DATABASE, "ilc_app") or revision != "0006_reliability":
            raise CaptureError("WRONG_DATABASE_OR_REVISION")
        sql(
            connection,
            "INSERT INTO ilc.sources VALUES ('synthetic_events','Synthetic capture') ON CONFLICT DO NOTHING",
        )
        sql(
            connection,
            "INSERT INTO ilc.runs(run_id,stage,started_at,status) VALUES (:run,'API_CAPTURE_P02A',:time,'RUNNING')",
            run=run_id,
            time=now(),
        )
        sql(
            connection,
            "INSERT INTO ilc.capture_checkpoints(capture_run_id,source_system,page_limit) VALUES (:run,'synthetic_events',5)",
            run=run_id,
        )
    return run_id


def drive(
    engine,
    url,
    run_id=None,
    stop_after=None,
    fail_before=None,
    scenario=None,
    timeout=2.0,
):
    url = endpoint_url(url)
    if not 0.1 <= timeout <= 10 or scenario not in (
        None,
        "http-503",
        "invalid-json",
        "delay",
    ):
        raise ValueError("Invalid recovery configuration")
    run_id = run_id or start_job(engine)
    invocation = "capture-invocation-" + str(uuid4())
    # Dedicated advisory session lock survives per-page commits, releases on death.
    with engine.connect() as guard:
        locked = sql(
            guard, "SELECT pg_try_advisory_lock(hashtextextended(:run,0))", run=run_id
        ).scalar_one()
        guard.rollback()
        if not locked:
            raise CaptureError("JOB_BUSY")
        try:
            with engine.begin() as connection:
                cp = checkpoint(connection, run_id)
                sql(
                    connection,
                    "INSERT INTO ilc.runs(run_id,stage,started_at,status) VALUES (:run,'CAPTURE_INVOCATION_P03',:time,'RUNNING')",
                    run=invocation,
                    time=now(),
                )
                if not cp["complete"]:
                    sql(
                        connection,
                        "UPDATE ilc.runs SET status='RUNNING',ended_at=NULL,error_category=NULL WHERE run_id=:run",
                        run=run_id,
                    )
            failure = None
            try:
                with httpx.Client(
                    trust_env=False,
                    follow_redirects=False,
                    headers={"Accept-Encoding": "identity"},
                ) as client:

                    def fetch(number, purpose, cursor=None):
                        path = (
                            url
                            if purpose == "SNAPSHOT_PROBE" or scenario is None
                            else url.removesuffix("/events") + "/scenarios/" + scenario
                        )
                        params = {"limit": cp["page_limit"]}
                        if cursor is not None:
                            params["cursor"] = cursor

                        def audit(attempt, status, body, error, started, ended):
                            with engine.begin() as connection:
                                sql(
                                    connection,
                                    """INSERT INTO ilc.capture_request_log
                                    (request_key,capture_run_id,invocation_run_id,page_number,request_attempt,purpose,
                                     request_url,requested_at,ended_at,http_status,response_body,response_sha256,error_category)
                                    VALUES (:key,:run,:invocation,:page,:attempt,:purpose,:url,:start,:end,:status,:body,:sha,:error)""",
                                    key=uuid4(),
                                    run=run_id,
                                    invocation=invocation,
                                    page=number,
                                    attempt=attempt,
                                    purpose=purpose,
                                    url=str(httpx.URL(path, params=params)),
                                    start=started,
                                    end=ended,
                                    status=status,
                                    body=body,
                                    sha=hashlib.sha256(body).hexdigest()
                                    if body is not None
                                    else None,
                                    error=error,
                                )

                        status, raw = request(
                            client, path, params, audit, timeout=timeout
                        )
                        if status != 200:
                            raise CaptureError("HTTP_ERROR:" + str(status))
                        return status, raw, str(httpx.URL(path, params=params))

                    if cp["last_page"] and not cp["complete"]:
                        _, probe, _ = fetch(0, "SNAPSHOT_PROBE")
                        validate_page(
                            probe,
                            cp["dataset_id"],
                            cp["api_total"],
                            None,
                            set(),
                            cp["page_limit"],
                            cp["source_system"],
                        )
                    seen = set()
                    while not cp["complete"]:
                        number = cp["last_page"] + 1
                        status, raw, actual_url = fetch(
                            number, "PAGE", cp["next_cursor"]
                        )
                        received = now()
                        data = validate_page(
                            raw,
                            cp["dataset_id"],
                            cp["api_total"],
                            cp["next_cursor"],
                            seen,
                            cp["page_limit"],
                            cp["source_system"],
                        )
                        commit_page_and_checkpoint(
                            engine,
                            before_commit=number == fail_before,
                            run_id=run_id,
                            invocation=invocation,
                            number=number,
                            url=actual_url,
                            cursor=cp["next_cursor"],
                            raw=raw,
                            status=status,
                            received=received,
                            data=data,
                        )
                        if data["next_cursor"]:
                            seen.add(data["next_cursor"])
                        with engine.connect() as connection:
                            cp = checkpoint(connection, run_id)
                        if stop_after is not None and cp["last_page"] >= stop_after:
                            raise CaptureError("SIMULATED_INTERRUPT_AFTER_COMMIT")
            except (CaptureError, httpx.HTTPError, SQLAlchemyError) as exc:
                failure = (
                    str(exc) if isinstance(exc, CaptureError) else type(exc).__name__
                )
            with engine.begin() as connection:
                cp = checkpoint(connection, run_id)
                actual = counts(connection, run_id)
                if (
                    cp["records"] != actual["records"]
                    or cp["last_page"] != actual["pages"]
                ):
                    failure = failure or "CHECKPOINT_COUNT_MISMATCH"
                if not failure and not cp["complete"]:
                    failure = "INCOMPLETE_CAPTURE"
                state = (
                    "SUCCEEDED"
                    if failure is None
                    else "PARTIAL"
                    if cp["records"]
                    else "FAILED"
                )
                for current, current_state in (
                    (run_id, state),
                    (invocation, "SUCCEEDED" if failure is None else "FAILED"),
                ):
                    sql(
                        connection,
                        "UPDATE ilc.runs SET status=:state,ended_at=:time,error_category=:error WHERE run_id=:run",
                        state=current_state,
                        time=now(),
                        error=failure,
                        run=current,
                    )
                requests = sql(
                    connection,
                    "SELECT count(*) FROM ilc.capture_request_log WHERE invocation_run_id=:run",
                    run=invocation,
                ).scalar_one()
            return {
                "capture_run_id": run_id,
                "invocation_run_id": invocation,
                "status": state,
                "error_category": failure,
                "last_page": cp["last_page"],
                "records": cp["records"],
                "complete": cp["complete"],
                "requests": requests,
            }
        finally:
            sql(
                guard, "SELECT pg_advisory_unlock(hashtextextended(:run,0))", run=run_id
            )
            guard.rollback()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=[TEST_DATABASE])
    parser.add_argument("--url", required=True)
    parser.add_argument("--resume-run")
    parser.add_argument("--stop-after-pages", type=int)
    parser.add_argument("--fail-before-commit-page", type=int)
    parser.add_argument("--scenario", choices=["http-503", "invalid-json", "delay"])
    parser.add_argument("--timeout", type=float, default=2)
    args = parser.parse_args()
    engine = test_engine(args.database)
    try:
        report = drive(
            engine,
            args.url,
            args.resume_run,
            args.stop_after_pages,
            args.fail_before_commit_page,
            args.scenario,
            args.timeout,
        )
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "SUCCEEDED" else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CaptureError, SQLAlchemyError, ValueError, OSError) as exc:
        print(json.dumps({"status": "FAILED", "error_category": type(exc).__name__}))
        raise SystemExit(1) from None

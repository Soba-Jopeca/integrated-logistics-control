"""Local bounded byte preservation and append-only extraction persistence."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.documents.parser import MAX_BYTES, VERSION, DocumentError, parse

STORE = Path(__file__).resolve().parents[2] / "data" / "documents"
MAX_STORE_BYTES = 32 * MAX_BYTES


def sql(c, query, **params):
    return c.execute(text(query), params)


def preserve(path, store=STORE):
    path = Path(path)
    if not path.exists():
        raise DocumentError("FILE_MISSING")
    if path.is_symlink() or not path.is_file():
        raise DocumentError("INVALID_FILE")
    with path.open("rb") as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise DocumentError("FILE_TOO_LARGE")
    if not raw:
        raise DocumentError("EMPTY_FILE")
    store.mkdir(parents=True, exist_ok=True)
    if store.is_symlink():
        raise DocumentError("INVALID_STORAGE")
    sha = hashlib.sha256(raw).hexdigest()
    target = store / sha
    if target.exists():
        if target.is_symlink() or target.read_bytes() != raw:
            raise DocumentError("STORAGE_HASH_MISMATCH")
    else:
        if (
            sum(p.stat().st_size for p in store.iterdir() if p.is_file()) + len(raw)
            > MAX_STORE_BYTES
        ):
            raise DocumentError("STORAGE_QUOTA")
        with target.open("xb") as f:
            f.write(raw)
    return raw, sha, str(target.resolve())


def extract_document(engine, path, envelope, store=STORE):
    """One run per call, stable version/input, fresh attempts/extractions on reexecution.

    P01 accepts initial versions only. Substitution is reserved for the next card.
    A missing/rejected file has a FAILED run, not a fictitious document version.
    """
    now = datetime.now(UTC)
    run = "document-" + str(uuid4())
    report = {"run_id": run, "parser_version": VERSION}
    with engine.begin() as c:
        sql(
            c,
            "INSERT INTO ilc.runs VALUES (:run,'DOCUMENT_EXTRACTION_P01',:now,NULL,'RUNNING',NULL)",
            run=run,
            now=now,
        )
    try:
        required = {
            "schema_version",
            "source_system",
            "document_id",
            "document_family_id",
            "version",
            "supersedes_document_id",
            "delivery_id",
            "media_type",
        }
        if set(envelope) != required or envelope["schema_version"] != "1.0":
            raise DocumentError("INVALID_ENVELOPE")
        for key in (
            "source_system",
            "document_id",
            "document_family_id",
            "delivery_id",
            "media_type",
        ):
            value = envelope[key]
            if not isinstance(value, str) or not value or value != value.strip():
                raise DocumentError("INVALID_ENVELOPE")
        if (
            type(envelope["version"]) is not int
            or envelope["version"] != 1
            or envelope["supersedes_document_id"] is not None
        ):
            raise DocumentError("INITIAL_VERSION_ONLY")
        raw, sha, reference = preserve(path, store)
        report["file_sha256"] = sha
        report["size_bytes"] = len(raw)
        identity_hash = hashlib.sha256(
            json.dumps(
                {"envelope": envelope, "file_sha256": sha}, sort_keys=True
            ).encode()
        ).hexdigest()
        with engine.begin() as c:
            # Serialize this service, including identity lookup and family creation.
            sql(c, "SELECT pg_advisory_xact_lock(4040101)")
            source = envelope["source_system"]
            sql(
                c,
                "INSERT INTO ilc.sources VALUES (:source,'Synthetic document fixtures') ON CONFLICT DO NOTHING",
                source=source,
            )
            existing = (
                sql(
                    c,
                    """SELECT d.*,i.normalized_sha256 FROM ilc.document_versions d
                JOIN ilc.inputs i USING(input_key) WHERE d.source_system=:source AND d.document_id=:id""",
                    source=source,
                    id=envelope["document_id"],
                )
                .mappings()
                .first()
            )
            duplicate = (
                existing is not None and existing["normalized_sha256"] == identity_hash
            )
            input_key = existing["input_key"] if duplicate else uuid4()
            attempt = uuid4()
            if not duplicate:
                sql(
                    c,
                    """INSERT INTO ilc.inputs VALUES (:key,:source,'DOCUMENT',:id,:ref,:sha,:now,:norm,:version,NULL)""",
                    key=input_key,
                    source=source,
                    id=envelope["document_id"],
                    ref=reference,
                    sha=sha,
                    now=now,
                    norm=identity_hash,
                    version=VERSION,
                )
            receipt = uuid4()
            sql(
                c,
                "INSERT INTO ilc.receipts VALUES (:key,:input,:now,:ref,:sha)",
                key=receipt,
                input=input_key,
                now=now,
                ref=reference,
                sha=sha,
            )
            category = None
            if existing is not None and not duplicate:
                category = "IDENTITY_CONFLICT"
            elif envelope["media_type"] not in ("application/pdf", "application/xml"):
                category = "UNSUPPORTED_FORMAT"
            delivery = sql(
                c,
                "SELECT delivery_key FROM ilc.deliveries WHERE delivery_id=:id",
                id=envelope["delivery_id"],
            ).scalar()
            if category is None and delivery is None:
                category = "INVALID_REFERENCE"
            if category is None and not duplicate:
                occupied = sql(
                    c,
                    "SELECT family_key FROM ilc.document_families WHERE source_system=:source AND document_family_id=:id",
                    source=source,
                    id=envelope["document_family_id"],
                ).scalar()
                if occupied:
                    category = "FAMILY_CONFLICT"
            sql(
                c,
                """INSERT INTO ilc.attempts VALUES (:key,:input,:run,:receipt,:now,:now,:outcome,:error)""",
                key=attempt,
                input=input_key,
                run=run,
                receipt=receipt,
                now=now,
                outcome="REJECTED"
                if category
                else ("DUPLICATE" if duplicate else "ACCEPTED"),
                error=category,
            )
            if category:
                report.update(status="FAILED", error_category=category)
            else:
                if duplicate:
                    document = existing["document_key"]
                else:
                    document, family = uuid4(), uuid4()
                    sql(
                        c,
                        "INSERT INTO ilc.document_families VALUES (:key,:source,:id,:delivery)",
                        key=family,
                        source=source,
                        id=envelope["document_family_id"],
                        delivery=delivery,
                    )
                    sql(
                        c,
                        """INSERT INTO ilc.document_versions
                        (document_key,family_key,source_system,delivery_key,document_id,version,
                         supersedes_document_key,schema_version,media_type,file_sha256,file_reference,
                         file_size_bytes,input_key,accepted_attempt_id,accepted_at)
                        VALUES (:key,:family,:source,:delivery,:id,1,NULL,'1.0',:media,:sha,:ref,:size,:input,:attempt,:now)""",
                        key=document,
                        family=family,
                        source=source,
                        delivery=delivery,
                        id=envelope["document_id"],
                        media=envelope["media_type"],
                        sha=sha,
                        ref=reference,
                        size=len(raw),
                        input=input_key,
                        attempt=attempt,
                        now=now,
                    )
                    sql(
                        c,
                        "INSERT INTO ilc.document_validities VALUES (:key,:family,:doc,:now,NULL)",
                        key=uuid4(),
                        family=family,
                        doc=document,
                        now=now,
                    )
                fields = dict.fromkeys(
                    (
                        "declared_delivery_id",
                        "delivered_at",
                        "received_quantity",
                        "quantity_unit",
                        "receiver_name",
                    )
                )
                try:
                    fields = parse(raw, envelope["media_type"])
                    outcome, error = "EXTRACTED", None
                except DocumentError as exc:
                    outcome, error = "PARSING_FAILED", str(exc)
                extraction = uuid4()
                sql(
                    c,
                    """INSERT INTO ilc.extractions VALUES
                    (:key,:doc,:input,:attempt,:version,:outcome,:now,:error,
                     :declared_delivery_id,:delivered_at,:received_quantity,:quantity_unit,:receiver_name)""",
                    key=extraction,
                    doc=document,
                    input=input_key,
                    attempt=attempt,
                    version=VERSION,
                    outcome=outcome,
                    now=now,
                    error=error,
                    **fields,
                )
                report.update(
                    status="SUCCEEDED" if outcome == "EXTRACTED" else "FAILED",
                    error_category=error,
                    document_key=str(document),
                    input_key=str(input_key),
                    extraction_key=str(extraction),
                    duplicate=duplicate,
                    outcome=outcome,
                    fields=fields,
                    missing_fields=[k for k, v in fields.items() if v is None],
                )
            sql(
                c,
                "UPDATE ilc.runs SET ended_at=:now,status=:status,error_category=:error WHERE run_id=:run",
                now=datetime.now(UTC),
                status=report["status"],
                error=report.get("error_category"),
                run=run,
            )
    except DocumentError as exc:
        report.update(status="FAILED", error_category=str(exc))
        with engine.begin() as c:
            sql(
                c,
                "UPDATE ilc.runs SET ended_at=:now,status='FAILED',error_category=:error WHERE run_id=:run",
                now=datetime.now(UTC),
                error=str(exc),
                run=run,
            )
    except (SQLAlchemyError, OSError):
        # Transaction rolled back; never publish SQL, file contents or credentials.
        with engine.begin() as c:
            sql(
                c,
                "UPDATE ilc.runs SET ended_at=:now,status='FAILED',error_category='PERSISTENCE_ERROR' WHERE run_id=:run",
                now=datetime.now(UTC),
                run=run,
            )
        raise DocumentError("PERSISTENCE_ERROR") from None
    return report

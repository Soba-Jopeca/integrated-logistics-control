"""Bounded uploads and read models; never infer a production database target."""

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import text

from scripts.migration_config import TEST_DATABASE, test_engine
from src.documents.parser import MAX_BYTES
from src.documents.service import extract_document
from src.documents.validation import evaluate, regularity


class AppError(Exception):
    """Public, credential-free failure."""


def connect(database):
    if database != TEST_DATABASE:
        raise AppError("Selecione explicitamente o banco de teste autorizado.")
    return test_engine(database)


def filter_deliveries(rows, identifier="", physical="Todos", documentary="Todos"):
    return [
        r
        for r in rows
        if identifier.strip().casefold() in r["delivery_id"].casefold()
        and (physical == "Todos" or r["physical_state"] == physical)
        and (documentary == "Todos" or r["documentary_state"] == documentary)
    ]


def list_deliveries(engine):
    # One row per delivery; never join events x documents into this list.
    with engine.connect() as c:
        ids = (
            c.execute(
                text("SELECT delivery_id FROM ilc.deliveries ORDER BY delivery_id")
            )
            .scalars()
            .all()
        )
    rows = []
    for identifier in ids:
        row = regularity(engine, identifier)
        row["documentary_state"] = (
            "SEM_DOCUMENTO"
            if row["current_documents"] == 0
            else "REGULAR"
            if row["regular"]
            else "PENDENTE"
        )
        rows.append(row)
    return rows, datetime.now(UTC)


def details(engine, identifier):
    queries = {
        "Decisões de conclusão": "SELECT x.decision_number,x.decision_type,x.decided_at,x.author,x.reason FROM ilc.completion_decisions x JOIN ilc.deliveries d USING(delivery_key) WHERE d.delivery_id=:id ORDER BY x.decision_number",
        "Conflitos e resoluções": "SELECT f.conflict_type,f.conflict_key,r.resolution_key FROM ilc.conflicts f JOIN ilc.deliveries d USING(delivery_key) LEFT JOIN ilc.conflict_resolutions r USING(conflict_key) WHERE d.delivery_id=:id",
        "Eventos": "SELECT e.event_id,e.event_type,e.occurred_at,e.accepted_at FROM ilc.events e JOIN ilc.deliveries d USING(delivery_key) WHERE d.delivery_id=:id ORDER BY e.occurred_at,e.event_id",
        "Comprovantes e vigência": "SELECT v.document_id,v.source_system,v.version,v.media_type,v.accepted_at,t.valid_from,t.valid_to FROM ilc.document_versions v JOIN ilc.deliveries d USING(delivery_key) JOIN ilc.document_validities t USING(document_key) WHERE d.delivery_id=:id ORDER BY v.accepted_at,v.document_id",
        "Extrações": "SELECT v.document_id,x.extractor_version,x.outcome,x.error_category,x.extracted_at,x.declared_delivery_id,x.delivered_at,x.received_quantity,x.quantity_unit,x.receiver_name FROM ilc.extractions x JOIN ilc.document_versions v USING(document_key) JOIN ilc.deliveries d ON d.delivery_key=v.delivery_key WHERE d.delivery_id=:id ORDER BY x.extracted_at",
        "Avaliações e histórico": "SELECT v.document_id,e.evaluation_number,e.result,e.rules_version,e.evaluated_at,t.valid_from,t.valid_to FROM ilc.evaluations e JOIN ilc.document_versions v USING(document_key) JOIN ilc.deliveries d ON d.delivery_key=v.delivery_key LEFT JOIN ilc.evaluation_validities t USING(evaluation_key) WHERE d.delivery_id=:id ORDER BY e.evaluated_at",
        "Motivos": "SELECT v.document_id,e.evaluation_number,r.code,r.affected_field,r.detail FROM ilc.evaluation_reasons r JOIN ilc.evaluations e USING(evaluation_key) JOIN ilc.document_versions v USING(document_key) JOIN ilc.deliveries d ON d.delivery_key=v.delivery_key WHERE d.delivery_id=:id ORDER BY e.evaluated_at,r.code",
    }
    with engine.begin() as c:
        c.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
        return {
            title: [dict(r) for r in c.execute(text(q), {"id": identifier}).mappings()]
            for title, q in queries.items()
        }


def validate_upload(name, raw, envelope):
    suffix = Path(name).suffix.lower()
    media = {".pdf": "application/pdf", ".xml": "application/xml"}
    if suffix not in media:
        raise AppError("Formato não permitido. Use PDF textual ou XML sintético.")
    if not raw:
        raise AppError("O arquivo está vazio.")
    if len(raw) > MAX_BYTES:
        raise AppError("Arquivo excede o limite de 1 MiB.")
    if not isinstance(envelope, dict) or envelope.get("media_type") != media[suffix]:
        raise AppError("O tipo do envelope deve corresponder ao arquivo.")
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
    if set(envelope) != required or envelope.get("schema_version") != "1.0":
        raise AppError(
            "Envelope inválido: confira os oito campos e schema_version 1.0."
        )
    for field in ("source_system", "document_id", "document_family_id", "delivery_id"):
        value = envelope[field]
        if (
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
            or len(value) > 200
        ):
            raise AppError(
                "Envelope inválido: identificadores devem ter de 1 a 200 caracteres, sem espaços nas extremidades."
            )
    version, previous = envelope["version"], envelope["supersedes_document_id"]
    if (
        type(version) is not int
        or version < 1
        or (version == 1 and previous is not None)
        or (
            version > 1
            and (
                not isinstance(previous, str)
                or not previous.strip()
                or previous != previous.strip()
            )
        )
    ):
        raise AppError("Cadeia de versões inválida no envelope.")


def process_upload(engine, name, raw, envelope, store=None):
    validate_upload(name, raw, envelope)
    with TemporaryDirectory(prefix="ilc-upload-") as temp:
        # Ignore the untrusted client path; the existing service stores by hash.
        path = Path(temp) / ("upload" + Path(name).suffix.lower())
        path.write_bytes(raw)
        kwargs = {} if store is None else {"store": store}
        extraction = extract_document(engine, path, envelope, **kwargs)
    evaluation = None
    if extraction.get("document_key"):
        # Parsing failures also need a persisted, reasoned evaluation.
        evaluation = evaluate(engine, extraction["document_key"])
    return {"extraction": extraction, "evaluation": evaluation}

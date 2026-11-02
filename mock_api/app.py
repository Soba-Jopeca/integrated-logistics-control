"""Snapshot sintetico paginado sem acesso ao banco."""

import base64
import binascii
import hashlib
import json
import re
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints

from mock_api.failures import router as failures_router
from mock_api.pagination import paginate

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests/fixtures/synthetic/v1/valid/events.jsonl"
)


Identifier = Annotated[str, StringConstraints(strict=True, pattern=r"^\S(?:.*\S)?$")]


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"]
    source_system: Identifier
    event_id: Identifier
    delivery_id: Identifier
    event_type: Literal["DISPATCHED", "IN_TRANSIT", "DELIVERED"]
    occurred_at: AwareDatetime
    notes: str | None = None


class EventPage(BaseModel):
    items: list[Event]
    total: int
    dataset_id: str
    next_cursor: str | None
    has_more: bool


def page_events(events: list[dict], offset: int, limit: int):
    """Retorna a pagina de eventos e a proxima posicao."""
    # Use paginate com os tres argumentos recebidos e retorne o resultado.
    return paginate(events, offset, limit)


def encode_cursor(dataset_id: str, offset: int) -> str:
    raw = json.dumps([1, dataset_id, offset], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(token: str, dataset_id: str, total: int) -> int:
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", token):
            raise ValueError
        raw = base64.b64decode(
            token + "=" * (-len(token) % 4), altchars=b"-_", validate=True
        )
        value = json.loads(raw)
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError
        version, snapshot, offset = value
        if type(version) is not int or version != 1 or snapshot != dataset_id:
            raise ValueError
        if type(offset) is not int or not 0 < offset < total:
            raise ValueError
        if encode_cursor(dataset_id, offset) != token:
            raise ValueError
        return offset
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise HTTPException(400, detail="INVALID_CURSOR") from exc


def create_app(fixture_path: Path = FIXTURE) -> FastAPI:
    raw = fixture_path.read_bytes()
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    ordered = sorted(
        enumerate(records),
        key=lambda pair: (pair[1]["source_system"], pair[1]["event_id"], pair[0]),
    )
    snapshot = json.dumps(
        [record for _, record in ordered], ensure_ascii=False
    ).encode()
    dataset_id = hashlib.sha256(raw).hexdigest()
    api = FastAPI(title="ILC - API simulada de eventos", version="0.1.0")

    @api.get(
        "/events",
        response_model=EventPage,
        responses={400: {"description": "Cursor invalido ou de outro snapshot"}},
        description=(
            "Fixture valid/events.jsonl integral, sem deduplicacao. Ordem: "
            "source_system, event_id, posicao original. Snapshot fixo no inicio. "
            "Termino: next_cursor=null e has_more=false. Limite entre 1 e 100."
        ),
    )
    def get_events(
        limit: Annotated[int, Query(ge=1, le=100)] = 5,
        cursor: Annotated[str | None, Query(max_length=256)] = None,
    ) -> EventPage:
        events = json.loads(snapshot)
        offset = 0 if cursor is None else decode_cursor(cursor, dataset_id, len(events))
        items, next_offset = page_events(events, offset, limit)
        return EventPage(
            items=items,
            total=len(events),
            dataset_id=dataset_id,
            next_cursor=None
            if next_offset is None
            else encode_cursor(dataset_id, next_offset),
            has_more=next_offset is not None,
        )

    api.include_router(failures_router)
    return api


app = create_app()

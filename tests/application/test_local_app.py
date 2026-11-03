"""UI/service contract checks; controlled doubles are not PostgreSQL/browser evidence."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

from src.application import service

ENV = {
    "schema_version": "1.0",
    "source_system": "synthetic",
    "document_id": "D1",
    "document_family_id": "F1",
    "version": 1,
    "supersedes_document_id": None,
    "delivery_id": "ENT-001",
    "media_type": "application/xml",
}
ROWS = [
    {
        "delivery_id": "ENT-001",
        "physical_state": "DELIVERED",
        "completion_contested": False,
        "documentary_state": "SEM_DOCUMENTO",
        "current_documents": 0,
        "regular": False,
    },
    {
        "delivery_id": "ENT-002",
        "physical_state": "NOT_CONFIRMED",
        "completion_contested": False,
        "documentary_state": "PENDENTE",
        "current_documents": 1,
        "regular": False,
    },
]


def test_filters_independent():
    assert (
        service.filter_deliveries(ROWS, " ent-001 ", "DELIVERED", "SEM_DOCUMENTO")
        == ROWS[:1]
    )
    assert service.filter_deliveries(ROWS, "ENT-001", "NOT_CONFIRMED") == []
    assert service.filter_deliveries(ROWS, documentary="PENDENTE") == ROWS[1:]
    assert service.filter_deliveries(ROWS, "' OR 1=1 --") == []


@pytest.mark.parametrize(
    "name,raw,env",
    [
        ("a.exe", b"x", ENV),
        ("a.xml", b"", ENV),
        ("a.xml", b"x" * (service.MAX_BYTES + 1), ENV),
        ("a.pdf", b"x", ENV),
        ("a.xml", b"x", []),
        ("a.xml", b"x", dict(ENV, version=True)),
        ("a.xml", b"x", dict(ENV, version=2)),
        ("a.xml", b"x", dict(ENV, source_system=" x")),
    ],
    ids=[
        "unsupported-format",
        "empty-file",
        "over-size-limit",
        "media-mismatch",
        "non-object-envelope",
        "boolean-version",
        "missing-predecessor",
        "untrimmed-source",
    ],
)
def test_reject_upload_before_writes(name, raw, env, monkeypatch):
    write = MagicMock()
    monkeypatch.setattr(service, "extract_document", write)
    with pytest.raises(service.AppError):
        service.process_upload(None, name, raw, env)
    write.assert_not_called()


def test_upload_boundary_and_safe_path():
    service.validate_upload("../../a.xml", b"x" * service.MAX_BYTES, ENV)


@pytest.mark.parametrize("outcome", ["EXTRACTED", "PARSING_FAILED"])
def test_existing_services_reused_and_temp_removed(monkeypatch, outcome):
    paths = []

    def extract(engine, path, envelope, **kwargs):
        paths.append(path)
        assert path.name == "upload.xml" and path.read_bytes() == b"synthetic"
        return {"document_key": "doc-key", "outcome": outcome, "status": "SUCCEEDED"}

    evaluate = MagicMock(return_value={"result": "REVIEW_REQUIRED", "reasons": []})
    monkeypatch.setattr(service, "extract_document", extract)
    monkeypatch.setattr(service, "evaluate", evaluate)
    result = service.process_upload(None, "../../x.xml", b"synthetic", ENV)
    assert result["evaluation"]["result"] == "REVIEW_REQUIRED"
    evaluate.assert_called_once_with(None, "doc-key")
    assert not paths[0].exists()


def test_rejected_identity_not_evaluated(monkeypatch):
    monkeypatch.setattr(
        service,
        "extract_document",
        lambda *a, **k: {"status": "FAILED", "error_category": "IDENTITY_CONFLICT"},
    )
    evaluate = MagicMock()
    monkeypatch.setattr(service, "evaluate", evaluate)
    assert service.process_upload(None, "x.xml", b"x", ENV)["evaluation"] is None
    evaluate.assert_not_called()


def test_explicit_test_database():
    with pytest.raises(service.AppError):
        service.connect("ilc")


def test_list_has_no_event_document_fanout(monkeypatch):
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.scalars.return_value.all.return_value = [
        "ENT-001",
        "ENT-002",
    ]
    monkeypatch.setattr(
        service,
        "regularity",
        lambda engine, identifier: dict(
            next(r for r in ROWS if r["delivery_id"] == identifier)
        ),
    )
    rows, consulted = service.list_deliveries(engine)
    assert [r["delivery_id"] for r in rows] == ["ENT-001", "ENT-002"]
    query = str(connection.execute.call_args.args[0])
    assert "JOIN" not in query
    assert consulted.tzinfo is not None


def app(monkeypatch):
    from datetime import UTC, datetime

    monkeypatch.setenv("ILC_APP_DATABASE", "ilc_f2p02b_test")
    monkeypatch.setattr(service, "connect", lambda database: MagicMock())
    monkeypatch.setattr(
        service, "list_deliveries", lambda engine: (ROWS, datetime.now(UTC))
    )
    monkeypatch.setattr(service, "details", lambda *args: {"Eventos": []})
    return AppTest.from_file(str(Path("app/local_app.py").resolve()))


def test_ui_filter_and_separate_states(monkeypatch):
    at = app(monkeypatch).run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 2
    at.text_input[0].set_value("ENT-001").run()
    assert len(at.dataframe[0].value) == 1
    assert any("SEM_DOCUMENTO" in str(x.value) for x in at.markdown)
    at.selectbox[0].set_value("NOT_CONFIRMED").run()
    assert at.info[0].value == "Nenhuma entrega corresponde aos filtros."


def test_db_outage_is_visible_not_empty_or_success(monkeypatch):
    at = app(monkeypatch)

    def unavailable(engine):
        raise RuntimeError("postgresql://private:secret@host/database")

    monkeypatch.setattr(service, "list_deliveries", unavailable)
    at.run()
    assert not at.exception
    assert "Não foi possível" in at.error[0].value
    assert "secret" not in at.error[0].value
    assert len(at.info) == 0 and len(at.success) == 0


def test_refresh_reads_again(monkeypatch):
    from datetime import UTC, datetime

    at = app(monkeypatch)
    calls = []

    def read(engine):
        calls.append(1)
        return ROWS[: len(calls)], datetime.now(UTC)

    monkeypatch.setattr(service, "list_deliveries", read)
    at.run()
    assert len(at.dataframe[0].value) == 1
    at.button[0].click().run()
    assert len(at.dataframe[0].value) == 2

"""Offline format controls. Four fixture cases await Joao's central edit."""

import json
from pathlib import Path

import pytest

from src.documents.parser import MAX_BYTES, DocumentError, normalize_delivered_at, parse
from src.documents.service import preserve

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/documents/v1"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text())


@pytest.mark.parametrize("name,expected", EXPECTED.items())
def test_fixed_fixtures(name, expected):
    raw = (FIXTURES / name).read_bytes()
    media = "application/pdf" if name.endswith("pdf") else "application/xml"
    if isinstance(expected, str):
        with pytest.raises(DocumentError, match=expected):
            parse(raw, media)
    else:
        result = parse(raw, media)
        result["delivered_at"] = (
            result["delivered_at"].isoformat().replace("+00:00", "Z")
        )
        assert result == expected


def test_empty_fields_are_null():
    assert all(
        v is None for v in parse(b"<delivery_receipt/>", "application/xml").values()
    )


@pytest.mark.parametrize("value", ["-1", "1.2", "true", "2147483648"])
def test_invalid_quantity(value):
    with pytest.raises(DocumentError, match="INVALID_FIELD_TYPE"):
        parse(
            f"<delivery_receipt><received_quantity>{value}</received_quantity></delivery_receipt>".encode(),
            "application/xml",
        )


def test_zero_is_not_null():
    assert (
        parse(
            b"<delivery_receipt><received_quantity>0</received_quantity></delivery_receipt>",
            "application/xml",
        )["received_quantity"]
        == 0
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"<!DOCTYPE delivery_receipt><delivery_receipt/>",
        b'<!DOCTYPE delivery_receipt [<!ENTITY x "bomb">]><delivery_receipt>&x;</delivery_receipt>',
    ],
)
def test_dtd_and_entities_forbidden(raw):
    with pytest.raises(DocumentError, match="XML_SECURITY_BLOCKED"):
        parse(raw, "application/xml")


@pytest.mark.parametrize(
    "raw",
    [
        b"<other/>",
        b"<delivery_receipt><receiver_name>A</receiver_name><receiver_name>B</receiver_name></delivery_receipt>",
    ],
)
def test_ambiguous_structure(raw):
    with pytest.raises(DocumentError, match="INVALID_XML_STRUCTURE"):
        parse(raw, "application/xml")


def test_size_limit():
    with pytest.raises(DocumentError, match="FILE_TOO_LARGE"):
        parse(b"x" * (MAX_BYTES + 1), "application/pdf")


def test_unsupported():
    with pytest.raises(DocumentError, match="UNSUPPORTED_FORMAT"):
        parse(b"data", "text/plain")


def test_missing_and_storage_hash(tmp_path):
    with pytest.raises(DocumentError, match="FILE_MISSING"):
        preserve(tmp_path / "missing", tmp_path / "store")
    source = tmp_path / "source"
    source.write_bytes(b"synthetic")
    raw, sha, ref = preserve(source, tmp_path / "store")
    assert Path(ref).name == sha and Path(ref).read_bytes() == raw
    assert preserve(source, tmp_path / "store") == (raw, sha, ref)
    Path(ref).write_bytes(b"corrupt")
    with pytest.raises(DocumentError, match="STORAGE_HASH_MISMATCH"):
        preserve(source, tmp_path / "store")


def test_empty_and_oversized_not_stored(tmp_path):
    source = tmp_path / "source"
    for raw, category in [
        (b"", "EMPTY_FILE"),
        (b"x" * (MAX_BYTES + 1), "FILE_TOO_LARGE"),
    ]:
        source.write_bytes(raw)
        with pytest.raises(DocumentError, match=category):
            preserve(source, tmp_path / "store")
    assert not (tmp_path / "store").exists()


def test_timestamp_requires_timezone():
    with pytest.raises(DocumentError, match="INVALID_FIELD_TYPE"):
        normalize_delivered_at("2026-10-16T14:00:00")

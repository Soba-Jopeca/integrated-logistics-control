"""Rules tested independently of persistence; author comparison remains explicit."""

from datetime import UTC, datetime, timedelta

import pytest

from src.documents.validation import reasons_for, same_utc_minute

TIME = datetime(2026, 10, 16, 17, tzinfo=UTC)
DELIVERY = {"delivery_id": "ENT", "expected_quantity": 10, "quantity_unit": "VOLUME"}
COMPLETION = {"occurred_at": TIME}
VALID = {
    "outcome": "EXTRACTED",
    "declared_delivery_id": "ENT",
    "delivered_at": TIME,
    "received_quantity": 10,
    "quantity_unit": "VOLUME",
    "receiver_name": "Pessoa",
}


def test_consistent():
    assert reasons_for(VALID, DELIVERY, COMPLETION) == []


@pytest.mark.parametrize(
    "seconds,expected", [(0, True), (59, True), (60, False), (-1, False)]
)
def test_utc_minute(seconds, expected):
    assert same_utc_minute(TIME + timedelta(seconds=seconds), TIME) is expected


def test_equivalent_timezone():
    assert same_utc_minute(datetime.fromisoformat("2026-10-16T14:00:59-03:00"), TIME)


@pytest.mark.parametrize(
    "field",
    ["declared_delivery_id", "received_quantity", "quantity_unit", "receiver_name"],
)
def test_required_without_completion(field):
    reasons = reasons_for(dict(VALID, **{field: None}), DELIVERY, None)
    assert {"MISSING_REQUIRED_FIELD", "DELIVERY_NOT_CONFIRMED"} == {
        r["code"] for r in reasons
    }


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("received_quantity", 9, "VALUE_MISMATCH"),
        ("quantity_unit", "BOX", "VALUE_MISMATCH"),
        ("declared_delivery_id", "OTHER", "REFERENCE_MISMATCH"),
    ],
)
def test_divergence_without_time_rule(field, value, code):
    reasons = reasons_for(dict(VALID, **{field: value}), DELIVERY, None)
    assert code in {r["code"] for r in reasons}


def test_invalid_reference():
    assert reasons_for(VALID, None, None)[0]["code"] == "INVALID_REFERENCE"


def test_parsing_failed():
    assert (
        reasons_for(
            {"outcome": "PARSING_FAILED", "error_category": "PARSING_ERROR"},
            DELIVERY,
            None,
        )[0]["code"]
        == "PARSING_ERROR"
    )


def test_contested_blocks_without_time_comparison():
    reasons = reasons_for(VALID, DELIVERY, COMPLETION, contested=True)
    assert reasons == [
        {
            "code": "DELIVERY_NOT_CONFIRMED",
            "field": "delivered_at",
            "detail": "COMPLETION_CONTESTED",
        }
    ]


def test_identity_conflict():
    reasons = reasons_for(VALID, DELIVERY, None, identity_conflict=True)
    assert "IDENTITY_CONFLICT" in {r["code"] for r in reasons}

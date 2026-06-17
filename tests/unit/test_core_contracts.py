from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from felts.core.schemas import ExtractedRecord, RawRecord, ValidationErrorDetail


def test_extracted_record_requires_canonical_source_and_entity() -> None:
    with pytest.raises(ValidationError):
        ExtractedRecord(source="CoinGecko", entity="markets", payload={})

    with pytest.raises(ValidationError):
        ExtractedRecord(source="coingecko", entity="coin-markets", payload={})


def test_extracted_record_requires_timezone_aware_timestamps() -> None:
    with pytest.raises(ValidationError):
        ExtractedRecord(
            source="coingecko",
            entity="markets",
            payload={},
            extracted_at=datetime(2026, 1, 1),
        )


def test_extracted_record_payload_must_be_object() -> None:
    with pytest.raises(ValidationError):
        ExtractedRecord.model_validate({"source": "coingecko", "entity": "markets", "payload": []})


def test_raw_record_can_hold_invalid_validation_details() -> None:
    record = RawRecord(
        id="raw-1",
        source="coingecko",
        entity="markets",
        payload={"price": "bad"},
        extracted_at=datetime(2026, 1, 1, tzinfo=UTC),
        batch_id="batch-1",
        is_valid=False,
        validation_errors=[
            ValidationErrorDetail(
                path="price",
                message="Input should be a valid number",
                type="float_parsing",
            )
        ],
    )

    assert record.validation_errors[0].path == "price"
    assert record.is_valid is False


def test_source_record_id_accepts_arbitrary_text_within_length_limit() -> None:
    record = ExtractedRecord(
        source="coingecko",
        entity="markets",
        source_record_id="https://api.example.test/coins/bitcoin?currency=usd",
        payload={"id": "bitcoin"},
    )

    assert record.source_record_id == "https://api.example.test/coins/bitcoin?currency=usd"

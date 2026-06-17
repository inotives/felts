from datetime import UTC, datetime, timedelta

from felts.core.schemas import canonical_payload_hash, make_raw_record_id


def test_raw_record_id_is_stable_for_same_source_identity_and_payload() -> None:
    observed_at = datetime(2026, 1, 1, tzinfo=UTC)
    payload = {"price": 1, "symbol": "btc"}

    first_id = make_raw_record_id(
        source="coingecko",
        entity="markets",
        source_record_id="bitcoin-usd",
        observed_at=observed_at,
        extracted_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
        payload=payload,
    )
    second_id = make_raw_record_id(
        source="coingecko",
        entity="markets",
        source_record_id="bitcoin-usd",
        observed_at=observed_at,
        extracted_at=datetime(2026, 1, 1, 2, tzinfo=UTC),
        payload={"symbol": "btc", "price": 1},
    )

    assert first_id == second_id


def test_raw_record_id_uses_extracted_at_only_when_no_better_identity_exists() -> None:
    payload = {"price": 1}
    first_extracted_at = datetime(2026, 1, 1, 1, tzinfo=UTC)
    second_extracted_at = first_extracted_at + timedelta(hours=1)

    first_id = make_raw_record_id(
        source="coingecko",
        entity="markets",
        extracted_at=first_extracted_at,
        payload=payload,
    )
    second_id = make_raw_record_id(
        source="coingecko",
        entity="markets",
        extracted_at=second_extracted_at,
        payload=payload,
    )

    assert first_id != second_id


def test_canonical_payload_hash_preserves_value_types() -> None:
    assert canonical_payload_hash({"a": 1, "b": "2"}) == canonical_payload_hash({"b": "2", "a": 1})
    assert canonical_payload_hash({"a": 1}) != canonical_payload_hash({"a": "1"})

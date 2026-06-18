"""CoinGecko REST extractor."""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from felts.core.exceptions import ExtractionError
from felts.core.extractors import BaseExtractor
from felts.core.extractors.rest import RestClient
from felts.core.schemas import ExtractedRecord
from felts.sources.coingecko.constants import (
    COINGECKO_SOURCE,
    ENDPOINTS,
    CoinGeckoEntity,
)


class CoinGeckoExtractor(BaseExtractor):
    """Extract Phase 02 CoinGecko entities into source-shaped records."""

    def __init__(
        self,
        *,
        client: RestClient,
        markets_vs_currency: str = "usd",
        markets_per_page: int = 250,
        markets_max_pages: int = 1,
    ) -> None:
        if not markets_vs_currency:
            msg = "markets_vs_currency is required"
            raise ExtractionError(msg)
        if markets_per_page < 1:
            msg = "markets_per_page must be greater than zero"
            raise ExtractionError(msg)
        if markets_max_pages < 1:
            msg = "markets_max_pages must be greater than zero"
            raise ExtractionError(msg)

        self.client = client
        self.markets_vs_currency = markets_vs_currency
        self.markets_per_page = markets_per_page
        self.markets_max_pages = markets_max_pages

    def extract(self) -> Iterable[ExtractedRecord]:
        for entity in ENDPOINTS:
            yield from self.extract_entity(entity)

    def extract_entity(self, entity: CoinGeckoEntity) -> list[ExtractedRecord]:
        match entity:
            case "coins_list":
                return self.extract_coins_list()
            case "asset_platforms_list":
                return self.extract_asset_platforms_list()
            case "global":
                return self.extract_global()
            case "global_defi":
                return self.extract_global_defi()
            case "coins_markets":
                return self.extract_coins_markets()

    def extract_coins_list(self) -> list[ExtractedRecord]:
        payloads = self._get_list("coins_list")
        return [self._list_item_record("coins_list", payload) for payload in payloads]

    def extract_asset_platforms_list(self) -> list[ExtractedRecord]:
        payloads = self._get_list("asset_platforms_list")
        return [self._list_item_record("asset_platforms_list", payload) for payload in payloads]

    def extract_global(self) -> list[ExtractedRecord]:
        payload = self._get_data_object("global")
        return [
            ExtractedRecord(
                source=COINGECKO_SOURCE,
                entity="global",
                payload=payload,
                source_record_id="global",
            )
        ]

    def extract_global_defi(self) -> list[ExtractedRecord]:
        payload = self._get_data_object("global_defi")
        return [
            ExtractedRecord(
                source=COINGECKO_SOURCE,
                entity="global_defi",
                payload=payload,
                source_record_id="global_defi",
            )
        ]

    def extract_coins_markets(self) -> list[ExtractedRecord]:
        records: list[ExtractedRecord] = []
        endpoint = ENDPOINTS["coins_markets"]
        for page in range(1, self.markets_max_pages + 1):
            data = self.client.get_json(
                endpoint.path,
                params={
                    "vs_currency": self.markets_vs_currency,
                    "per_page": self.markets_per_page,
                    "page": page,
                },
            )
            if not isinstance(data, list):
                msg = "CoinGecko coins_markets response must be a list"
                raise ExtractionError(msg)
            if not data:
                break
            page_records = [self._market_record(payload) for payload in data]
            records.extend(page_records)
            if len(data) < self.markets_per_page:
                break
        return records

    def _get_list(self, entity: CoinGeckoEntity) -> list[dict[str, Any]]:
        endpoint = ENDPOINTS[entity]
        data = self.client.get_json(endpoint.path)
        if not isinstance(data, list):
            msg = f"CoinGecko {entity} response must be a list"
            raise ExtractionError(msg)
        return [_ensure_object(entity=entity, payload=payload) for payload in data]

    def _get_data_object(self, entity: CoinGeckoEntity) -> dict[str, Any]:
        endpoint = ENDPOINTS[entity]
        data = self.client.get_json(endpoint.path)
        if not isinstance(data, dict) or not isinstance(data.get("data"), dict):
            msg = f"CoinGecko {entity} response must be an object with a data object"
            raise ExtractionError(msg)
        payload = data["data"]
        if not isinstance(payload, dict):
            msg = f"CoinGecko {entity} data field must be a JSON object"
            raise ExtractionError(msg)
        return payload

    def _list_item_record(
        self, entity: CoinGeckoEntity, payload: dict[str, Any]
    ) -> ExtractedRecord:
        source_record_id = payload.get("id")
        return ExtractedRecord(
            source=COINGECKO_SOURCE,
            entity=entity,
            payload=payload,
            source_record_id=str(source_record_id) if source_record_id is not None else None,
        )

    def _market_record(self, payload: Any) -> ExtractedRecord:
        payload = _ensure_object(entity="coins_markets", payload=payload)
        last_updated = payload.get("last_updated")
        return ExtractedRecord(
            source=COINGECKO_SOURCE,
            entity="coins_markets",
            payload=payload,
            source_record_id=str(payload["id"]) if payload.get("id") is not None else None,
            observed_at=_parse_datetime(last_updated) if isinstance(last_updated, str) else None,
        )


def _ensure_object(*, entity: str, payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    msg = f"CoinGecko {entity} item must be a JSON object"
    raise ExtractionError(msg)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=UTC)
    return parsed

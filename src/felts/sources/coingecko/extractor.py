"""CoinGecko REST extractor."""

import csv
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from felts.config.settings import REPO_ROOT
from felts.core.exceptions import ExtractionError
from felts.core.extractors import BaseExtractor
from felts.core.extractors.rest import RestClient
from felts.core.schemas import ExtractedRecord
from felts.sources.coingecko.constants import (
    COINGECKO_SOURCE,
    ENDPOINTS,
    CoinGeckoEntity,
)

DEFAULT_ASSET_PROVIDER_MAPPINGS_PATH = (
    REPO_ROOT / "transforms" / "seeds" / "felts" / "asset_provider_mappings.csv"
)


class CoinGeckoExtractor(BaseExtractor):
    """Extract CoinGecko entities into source-shaped records."""

    def __init__(
        self,
        *,
        client: RestClient,
        markets_vs_currency: str = "usd",
        markets_per_page: int = 250,
        markets_max_pages: int = 1,
        ohlc_days: int = 90,
        ohlc_coin_ids: tuple[str, ...] | None = None,
        asset_provider_mappings_path: Path = DEFAULT_ASSET_PROVIDER_MAPPINGS_PATH,
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
        if ohlc_days < 1:
            msg = "ohlc_days must be greater than zero"
            raise ExtractionError(msg)

        self.client = client
        self.markets_vs_currency = markets_vs_currency
        self.markets_per_page = markets_per_page
        self.markets_max_pages = markets_max_pages
        self.ohlc_days = ohlc_days
        self.ohlc_coin_ids = (
            tuple(ohlc_coin_ids)
            if ohlc_coin_ids is not None
            else load_default_coingecko_coin_ids(asset_provider_mappings_path)
        )

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
            case "coins_ohlc":
                return self.extract_coins_ohlc()
            case "coins_market_chart":
                return self.extract_coins_market_chart()

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

    def extract_coins_ohlc(self) -> list[ExtractedRecord]:
        records: list[ExtractedRecord] = []
        for coin_id in self.ohlc_coin_ids:
            data = self.client.get_json(
                ENDPOINTS["coins_ohlc"].path.format(coin_id=coin_id),
                params={
                    "vs_currency": self.markets_vs_currency,
                    "days": self.ohlc_days,
                    "interval": "daily",
                },
            )
            if not isinstance(data, list):
                msg = "CoinGecko coins_ohlc response must be a list"
                raise ExtractionError(msg)
            for row in data:
                records.append(self._ohlc_record(coin_id=coin_id, row=row))
        return records

    def extract_coins_market_chart(self) -> list[ExtractedRecord]:
        records: list[ExtractedRecord] = []
        for coin_id in self.ohlc_coin_ids:
            data = self.client.get_json(
                ENDPOINTS["coins_market_chart"].path.format(coin_id=coin_id),
                params={
                    "vs_currency": self.markets_vs_currency,
                    "days": self.ohlc_days,
                    "interval": "daily",
                },
            )
            series = _parse_market_chart_series(data)
            for row in series:
                records.append(self._market_chart_record(coin_id=coin_id, row=row))
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

    def _ohlc_record(self, *, coin_id: str, row: Any) -> ExtractedRecord:
        timestamp_ms, open_price, high_price, low_price, close_price = _parse_ohlc_row(row)
        payload = {
            "coin_id": coin_id,
            "vs_currency": self.markets_vs_currency,
            "days": self.ohlc_days,
            "interval": "daily",
            "timestamp_ms": timestamp_ms,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
        }
        return ExtractedRecord(
            source=COINGECKO_SOURCE,
            entity="coins_ohlc",
            payload=payload,
            observed_at=datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC),
            source_record_id=f"{coin_id}|{self.markets_vs_currency}|{timestamp_ms}",
        )

    def _market_chart_record(
        self, *, coin_id: str, row: tuple[int, float, float, float]
    ) -> ExtractedRecord:
        timestamp_ms, price, market_cap, total_volume = row
        payload = {
            "coin_id": coin_id,
            "vs_currency": self.markets_vs_currency,
            "days": self.ohlc_days,
            "interval": "daily",
            "timestamp_ms": timestamp_ms,
            "price": price,
            "market_cap": market_cap,
            "total_volume": total_volume,
        }
        return ExtractedRecord(
            source=COINGECKO_SOURCE,
            entity="coins_market_chart",
            payload=payload,
            observed_at=datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC),
            source_record_id=f"{coin_id}|{self.markets_vs_currency}|daily|{timestamp_ms}",
        )


def load_default_coingecko_coin_ids(
    path: Path = DEFAULT_ASSET_PROVIDER_MAPPINGS_PATH,
) -> tuple[str, ...]:
    seen: set[str] = set()
    coin_ids: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("provider_source") != "coingecko":
                continue
            coin_id = (row.get("provider_asset_id") or "").strip()
            if not coin_id or coin_id in seen:
                continue
            seen.add(coin_id)
            coin_ids.append(coin_id)
    return tuple(coin_ids)


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


def _parse_ohlc_row(row: Any) -> tuple[int, float, float, float, float]:
    if not isinstance(row, list) or len(row) != 5:
        msg = "CoinGecko coins_ohlc row must be a five-item array"
        raise ExtractionError(msg)

    timestamp_ms = _int_value(row[0], field_name="timestamp_ms")
    open_price = _float_value(row[1], field_name="open")
    high_price = _float_value(row[2], field_name="high")
    low_price = _float_value(row[3], field_name="low")
    close_price = _float_value(row[4], field_name="close")
    return (timestamp_ms, open_price, high_price, low_price, close_price)


def _parse_market_chart_series(data: Any) -> list[tuple[int, float, float, float]]:
    if not isinstance(data, dict):
        msg = "CoinGecko coins_market_chart response must be an object"
        raise ExtractionError(msg)

    prices = _parse_market_chart_metric_rows(field_name="prices", value=data.get("prices"))
    market_caps = _parse_market_chart_metric_rows(
        field_name="market_caps", value=data.get("market_caps")
    )
    total_volumes = _parse_market_chart_metric_rows(
        field_name="total_volumes", value=data.get("total_volumes")
    )
    timestamps = set(prices) | set(market_caps) | set(total_volumes)
    if (
        timestamps != set(prices)
        or timestamps != set(market_caps)
        or timestamps != set(total_volumes)
    ):
        msg = "CoinGecko coins_market_chart metrics must share the same timestamps"
        raise ExtractionError(msg)
    return [
        (
            timestamp_ms,
            prices[timestamp_ms],
            market_caps[timestamp_ms],
            total_volumes[timestamp_ms],
        )
        for timestamp_ms in sorted(timestamps)
    ]


def _parse_market_chart_metric_rows(*, field_name: str, value: Any) -> dict[int, float]:
    if not isinstance(value, list):
        msg = f"CoinGecko coins_market_chart {field_name} must be a list"
        raise ExtractionError(msg)
    rows: dict[int, float] = {}
    for row in value:
        if not isinstance(row, list) or len(row) != 2:
            msg = f"CoinGecko coins_market_chart {field_name} rows must be two-item arrays"
            raise ExtractionError(msg)
        timestamp_ms = _int_value(row[0], field_name="timestamp_ms", entity="coins_market_chart")
        metric_value = _float_value(row[1], field_name=field_name, entity="coins_market_chart")
        rows[timestamp_ms] = metric_value
    return rows


def _int_value(value: Any, *, field_name: str, entity: str = "coins_ohlc") -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        msg = f"CoinGecko {entity} {field_name} must be numeric"
        raise ExtractionError(msg)
    return int(value)


def _float_value(value: Any, *, field_name: str, entity: str = "coins_ohlc") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        msg = f"CoinGecko {entity} {field_name} must be numeric"
        raise ExtractionError(msg)
    return float(value)

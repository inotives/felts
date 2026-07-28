"""CCXT public exchange extractor."""

import csv
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from felts.config.settings import REPO_ROOT
from felts.core.exceptions import ConfigurationError, ExtractionError
from felts.core.extractors import BaseExtractor
from felts.core.schemas import ExtractedRecord
from felts.sources.ccxt.constants import CCXT_SOURCE, SUPPORTED_ENTITIES, CcxtEntity

DEFAULT_MARKET_UNIVERSE_PATH = (
    REPO_ROOT / "transforms" / "seeds" / "ccxt" / "ccxt_market_universe.csv"
)


@dataclass(frozen=True)
class CcxtMarket:
    exchange_id: str
    symbol: str
    base_asset: str
    quote_asset: str
    order_book_limit: int
    is_active: bool


class ExchangeClient(Protocol):
    def fetch_ticker(self, symbol: str) -> dict[str, Any]: ...

    def fetch_order_book(self, symbol: str, limit: int | None = None) -> dict[str, Any]: ...


class CcxtExtractor(BaseExtractor):
    """Extract provider-native ticker and order book snapshots."""

    def __init__(self, *, client: ExchangeClient, markets: Sequence[CcxtMarket]) -> None:
        self.client = client
        self.markets = tuple(market for market in markets if market.is_active)
        if not self.markets:
            msg = "at least one active CCXT market is required"
            raise ConfigurationError(msg)

    def extract(self) -> Iterable[ExtractedRecord]:
        for entity in SUPPORTED_ENTITIES:
            yield from self.extract_entity(entity)

    def extract_entity(self, entity: CcxtEntity) -> list[ExtractedRecord]:
        if entity not in SUPPORTED_ENTITIES:
            msg = f"unsupported CCXT entity: {entity}"
            raise ExtractionError(msg)
        if entity == "ticker":
            return [self._extract_ticker(market) for market in self.markets]
        return [self._extract_order_book(market) for market in self.markets]

    def _extract_ticker(self, market: CcxtMarket) -> ExtractedRecord:
        extracted_at = datetime.now(UTC)
        try:
            raw_response = self.client.fetch_ticker(market.symbol)
        except ExtractionError:
            raise
        except Exception as exc:
            msg = f"CCXT ticker extraction failed for {market.exchange_id} {market.symbol}"
            raise ExtractionError(msg) from exc
        observed_at = _resolve_observed_at(raw_response, extracted_at=extracted_at)
        payload = {
            "exchange_id": market.exchange_id,
            "symbol": market.symbol,
            "base_asset": market.base_asset,
            "quote_asset": market.quote_asset,
            "timestamp": raw_response.get("timestamp"),
            "datetime": raw_response.get("datetime"),
            "bid": raw_response.get("bid"),
            "ask": raw_response.get("ask"),
            "last": raw_response.get("last"),
            "open": raw_response.get("open"),
            "high": raw_response.get("high"),
            "low": raw_response.get("low"),
            "close": raw_response.get("close"),
            "base_volume": raw_response.get("baseVolume"),
            "quote_volume": raw_response.get("quoteVolume"),
            "vwap": raw_response.get("vwap"),
            "percentage": raw_response.get("percentage"),
            "raw_response": raw_response,
        }
        return ExtractedRecord(
            source=CCXT_SOURCE,
            entity="ticker",
            payload=payload,
            extracted_at=extracted_at,
            observed_at=observed_at,
            source_record_id=_source_record_id(
                entity="ticker",
                market=market,
                observed_at=observed_at,
            ),
        )

    def _extract_order_book(self, market: CcxtMarket) -> ExtractedRecord:
        extracted_at = datetime.now(UTC)
        try:
            raw_response = self.client.fetch_order_book(
                market.symbol,
                limit=market.order_book_limit,
            )
        except ExtractionError:
            raise
        except Exception as exc:
            msg = f"CCXT order_book extraction failed for {market.exchange_id} {market.symbol}"
            raise ExtractionError(msg) from exc
        observed_at = _resolve_observed_at(raw_response, extracted_at=extracted_at)
        bids = _levels(raw_response.get("bids"))
        asks = _levels(raw_response.get("asks"))
        payload = {
            "exchange_id": market.exchange_id,
            "symbol": market.symbol,
            "base_asset": market.base_asset,
            "quote_asset": market.quote_asset,
            "limit": market.order_book_limit,
            "timestamp": raw_response.get("timestamp"),
            "datetime": raw_response.get("datetime"),
            "nonce": raw_response.get("nonce"),
            "best_bid": _best_price(bids),
            "best_ask": _best_price(asks),
            "bids": bids,
            "asks": asks,
            "raw_response": raw_response,
        }
        return ExtractedRecord(
            source=CCXT_SOURCE,
            entity="order_book",
            payload=payload,
            extracted_at=extracted_at,
            observed_at=observed_at,
            source_record_id=_source_record_id(
                entity="order_book",
                market=market,
                observed_at=observed_at,
            ),
        )


def load_ccxt_markets(path: Path = DEFAULT_MARKET_UNIVERSE_PATH) -> tuple[CcxtMarket, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = tuple(reader)
    required_headers = {
        "exchange_id",
        "symbol",
        "base_asset",
        "quote_asset",
        "order_book_limit",
        "is_active",
    }
    if reader.fieldnames is None or not required_headers.issubset(reader.fieldnames):
        msg = (
            "CCXT market universe must include exchange_id, symbol, "
            "base_asset, quote_asset, order_book_limit, and is_active"
        )
        raise ConfigurationError(msg)
    markets: list[CcxtMarket] = []
    for row in rows:
        markets.append(
            CcxtMarket(
                exchange_id=_required_value(row, "exchange_id"),
                symbol=_required_value(row, "symbol"),
                base_asset=_required_value(row, "base_asset"),
                quote_asset=_required_value(row, "quote_asset"),
                order_book_limit=_parse_limit(_required_value(row, "order_book_limit")),
                is_active=_parse_bool(_required_value(row, "is_active")),
            )
        )
    return tuple(markets)


def _required_value(row: dict[str, str | None], field: str) -> str:
    value = row.get(field)
    if value is None or not value.strip():
        msg = f"CCXT market universe field {field} must be present"
        raise ConfigurationError(msg)
    return value.strip()


def _parse_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as exc:
        msg = f"invalid CCXT order_book_limit: {value}"
        raise ConfigurationError(msg) from exc
    if limit < 1:
        msg = "CCXT order_book_limit must be greater than zero"
        raise ConfigurationError(msg)
    return limit


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    msg = f"invalid CCXT is_active value: {value}"
    raise ConfigurationError(msg)


def _resolve_observed_at(payload: dict[str, Any], *, extracted_at: datetime) -> datetime:
    timestamp = payload.get("timestamp")
    if isinstance(timestamp, int | float):
        return datetime.fromtimestamp(float(timestamp) / 1000, tz=UTC)
    datetime_value = payload.get("datetime")
    if isinstance(datetime_value, str):
        return _parse_datetime(datetime_value)
    return extracted_at


def _parse_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        msg = f"invalid CCXT datetime value: {value}"
        raise ExtractionError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _levels(value: Any) -> list[list[float | int]]:
    if not isinstance(value, list):
        return []
    levels: list[list[float | int]] = []
    for level in value:
        if not isinstance(level, list) or len(level) < 2:
            continue
        price = level[0]
        amount = level[1]
        if isinstance(price, int | float) and isinstance(amount, int | float):
            levels.append([price, amount])
    return levels


def _best_price(levels: list[list[float | int]]) -> float | None:
    if not levels:
        return None
    price = levels[0][0]
    return float(price) if isinstance(price, int | float) else None


def _source_record_id(*, entity: CcxtEntity, market: CcxtMarket, observed_at: datetime) -> str:
    observed_at_iso = observed_at.astimezone(UTC).isoformat()
    return f"{entity}|{market.exchange_id}|{market.symbol}|{observed_at_iso}"

"""Minimal tolerant CCXT raw validation schemas."""

from datetime import datetime as DateTime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CcxtModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class TickerPayload(CcxtModel):
    exchange_id: str
    symbol: str
    base_asset: str
    quote_asset: str
    timestamp: int | None = None
    datetime: DateTime | None = None
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    base_volume: float | None = None
    quote_volume: float | None = None
    vwap: float | None = None
    percentage: float | None = None
    raw_response: dict[str, Any]


class OrderBookPayload(CcxtModel):
    exchange_id: str
    symbol: str
    base_asset: str
    quote_asset: str
    limit: int
    timestamp: int | None = None
    datetime: DateTime | None = None
    nonce: int | str | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    bids: list[list[float | int]]
    asks: list[list[float | int]]
    raw_response: dict[str, Any]

"""Minimal tolerant CoinGecko raw validation schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CoinGeckoModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class CoinsListPayload(CoinGeckoModel):
    id: str
    symbol: str
    name: str


class AssetPlatformsListPayload(CoinGeckoModel):
    id: str
    name: str


class GlobalPayload(CoinGeckoModel):
    active_cryptocurrencies: int
    markets: int
    total_market_cap: dict[str, float]


class GlobalDefiPayload(CoinGeckoModel):
    defi_market_cap: str
    eth_market_cap: str
    defi_to_eth_ratio: str


class CoinsMarketsPayload(CoinGeckoModel):
    id: str
    symbol: str
    name: str
    current_price: float | None = None
    last_updated: datetime | None = None

from datetime import UTC, datetime
from pathlib import Path

import pytest

from felts.core.exceptions import ExtractionError
from felts.sources.ccxt.extractor import CcxtExtractor, CcxtMarket, load_ccxt_markets


class FakeExchangeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int | None]] = []

    def fetch_ticker(self, symbol: str) -> dict[str, object]:
        self.calls.append(("fetch_ticker", symbol, None))
        return {
            "timestamp": 1735689600000,
            "datetime": "2025-01-01T00:00:00Z",
            "bid": 100000.0,
            "ask": 100010.0,
            "last": 100005.0,
            "open": 99000.0,
            "high": 101000.0,
            "low": 98000.0,
            "close": 100005.0,
            "baseVolume": 12.5,
            "quoteVolume": 1250000.0,
            "vwap": 100100.0,
            "percentage": 1.5,
        }

    def fetch_order_book(self, symbol: str, limit: int | None = None) -> dict[str, object]:
        self.calls.append(("fetch_order_book", symbol, limit))
        return {
            "nonce": 123,
            "bids": [[100000.0, 1.25], [99990.0, 0.5]],
            "asks": [[100010.0, 0.75], [100020.0, 1.0]],
        }


class BoomExchangeClient(FakeExchangeClient):
    def fetch_order_book(self, symbol: str, limit: int | None = None) -> dict[str, object]:
        raise RuntimeError("provider boom")


def test_load_ccxt_markets_reads_committed_contract(tmp_path: Path) -> None:
    path = tmp_path / "ccxt_market_universe.csv"
    path.write_text(
        "\n".join(
            [
                "exchange_id,symbol,base_asset,quote_asset,order_book_limit,is_active",
                "binance,BTC/USDT,BTC,USDT,20,true",
                "binance,ETH/USDT,ETH,USDT,20,false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    markets = load_ccxt_markets(path)

    assert len(markets) == 2
    assert markets[0].exchange_id == "binance"
    assert markets[0].symbol == "BTC/USDT"
    assert markets[0].order_book_limit == 20
    assert markets[1].is_active is False


def test_extract_ticker_uses_provider_timestamp() -> None:
    client = FakeExchangeClient()
    extractor = CcxtExtractor(
        client=client,
        markets=_markets(),
    )

    records = extractor.extract_entity("ticker")

    assert client.calls == [("fetch_ticker", "BTC/USDT", None)]
    assert len(records) == 1
    assert records[0].observed_at == datetime(2025, 1, 1, tzinfo=UTC)
    assert records[0].source_record_id == "ticker|binance|BTC/USDT|2025-01-01T00:00:00+00:00"
    assert records[0].payload["quote_volume"] == 1250000.0


def test_extract_order_book_falls_back_to_extraction_time() -> None:
    client = FakeExchangeClient()
    extractor = CcxtExtractor(
        client=client,
        markets=_markets(),
    )

    records = extractor.extract_entity("order_book")

    assert client.calls == [("fetch_order_book", "BTC/USDT", 20)]
    assert len(records) == 1
    assert records[0].observed_at == records[0].extracted_at
    assert records[0].payload["best_bid"] == 100000.0
    assert records[0].payload["best_ask"] == 100010.0
    assert records[0].source_record_id == (
        f"order_book|binance|BTC/USDT|{records[0].observed_at.astimezone(UTC).isoformat()}"
    )


def test_extract_order_book_normalizes_provider_exceptions() -> None:
    extractor = CcxtExtractor(
        client=BoomExchangeClient(),
        markets=_markets(),
    )

    with pytest.raises(ExtractionError, match="CCXT order_book extraction failed") as exc_info:
        extractor.extract_entity("order_book")
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) == "provider boom"


def _markets() -> tuple[CcxtMarket, ...]:
    return (
        CcxtMarket(
            exchange_id="binance",
            symbol="BTC/USDT",
            base_asset="BTC",
            quote_asset="USDT",
            order_book_limit=20,
            is_active=True,
        ),
    )

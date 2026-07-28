"""CCXT source constants."""

from typing import Literal

CcxtEntity = Literal["ticker", "order_book"]

CCXT_SOURCE = "ccxt"
SUPPORTED_ENTITIES: tuple[CcxtEntity, ...] = ("ticker", "order_book")

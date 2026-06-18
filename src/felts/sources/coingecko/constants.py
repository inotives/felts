"""CoinGecko source constants."""

from dataclasses import dataclass
from typing import Literal

CoinGeckoEntity = Literal[
    "coins_list",
    "asset_platforms_list",
    "global",
    "global_defi",
    "coins_markets",
]

COINGECKO_SOURCE = "coingecko"
SUPPORTED_ENTITIES: tuple[CoinGeckoEntity, ...] = (
    "coins_list",
    "asset_platforms_list",
    "global",
    "global_defi",
    "coins_markets",
)

DBT_SELECTORS: dict[CoinGeckoEntity, str] = {
    "coins_list": "stg_coingecko__coins_list+",
    "asset_platforms_list": "stg_coingecko__asset_platforms_list+",
    "global": "stg_coingecko__global+",
    "global_defi": "stg_coingecko__global_defi+",
    "coins_markets": "stg_coingecko__coins_markets+",
}

SCHEDULED_ENTITIES: tuple[CoinGeckoEntity, ...] = (
    "coins_list",
    "asset_platforms_list",
    "global",
    "global_defi",
)

COINGECKO_SOURCE_DEPLOYMENT_PREFIX = "coingecko"


@dataclass(frozen=True)
class CoinGeckoEndpoint:
    entity: CoinGeckoEntity
    path: str
    response_shape: Literal["list", "data_object"]
    source_record_id_field: str | None


ENDPOINTS: dict[CoinGeckoEntity, CoinGeckoEndpoint] = {
    "coins_list": CoinGeckoEndpoint("coins_list", "/coins/list", "list", "id"),
    "asset_platforms_list": CoinGeckoEndpoint(
        "asset_platforms_list", "/asset_platforms", "list", "id"
    ),
    "global": CoinGeckoEndpoint("global", "/global", "data_object", None),
    "global_defi": CoinGeckoEndpoint(
        "global_defi", "/global/decentralized_finance_defi", "data_object", None
    ),
    "coins_markets": CoinGeckoEndpoint("coins_markets", "/coins/markets", "list", "id"),
}

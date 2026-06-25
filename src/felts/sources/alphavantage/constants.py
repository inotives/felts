"""Generated Alphavantage source constants."""

from dataclasses import dataclass
from typing import Literal

ALPHAVANTAGE_SOURCE = "alphavantage"
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co"

ResponseShape = Literal["list", "object", "data_object", "keyed_object"]


@dataclass(frozen=True)
class Endpoint:
    path: str
    response_shape: ResponseShape
    records_path: str | None = None
    key_field: str | None = None
    id_fields: tuple[str, ...] = ()
    params: dict[str, str] | None = None
    runtime_params: tuple[str, ...] = ()


SUPPORTED_ENTITIES: tuple[str, ...] = (
    # scaffold: entities:start
    "time_series_daily",
    # scaffold: entities:end
)

ENDPOINTS: dict[str, Endpoint] = {
    # scaffold: endpoints:start
    "time_series_daily": Endpoint(
        path="/query",
        response_shape="keyed_object",
        records_path="Time Series (Daily)",
        key_field="trading_date",
        id_fields=("symbol", "trading_date"),
        params={"function": "TIME_SERIES_DAILY", "outputsize": "compact"},
        runtime_params=("symbol",),
    ),
    # scaffold: endpoints:end
}

DBT_SELECTORS = {entity: f"stg_alphavantage__{entity}+" for entity in SUPPORTED_ENTITIES}

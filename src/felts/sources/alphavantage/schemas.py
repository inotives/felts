"""Tolerant Alpha Vantage payload schemas."""

from pydantic import BaseModel, ConfigDict


class AlphavantageModel(BaseModel):
    model_config = ConfigDict(extra="allow")


# scaffold: schemas:start
class TimeSeriesDailyPayload(AlphavantageModel):
    symbol: str
    trading_date: str


# scaffold: schemas:end

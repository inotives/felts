"""CSV raw payload validation models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CsvRawPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    felts: dict[str, Any] = Field(alias="_felts")

    @field_validator("felts")
    @classmethod
    def _reject_extractor_validation_errors(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value.get("validation_errors"):
            msg = "CSV row failed extractor validation"
            raise ValueError(msg)
        return value

"""Source-shaped records emitted by extractors."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from felts.core.schemas.identifiers import (
    BATCH_ID_MAX_LENGTH,
    ENTITY_MAX_LENGTH,
    SOURCE_MAX_LENGTH,
    SOURCE_RECORD_ID_MAX_LENGTH,
    validate_identifier,
    validate_optional_text,
)


class ExtractedRecord(BaseModel):
    """A source-shaped record before validation and raw wrapping."""

    model_config = ConfigDict(frozen=True)

    source: str
    entity: str
    payload: dict[str, Any]
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    observed_at: datetime | None = None
    source_record_id: str | None = None
    batch_id: str | None = None

    @field_validator("source")
    @classmethod
    def _validate_source(cls, value: str) -> str:
        return validate_identifier(value, field_name="source", max_length=SOURCE_MAX_LENGTH)

    @field_validator("entity")
    @classmethod
    def _validate_entity(cls, value: str) -> str:
        return validate_identifier(value, field_name="entity", max_length=ENTITY_MAX_LENGTH)

    @field_validator("source_record_id")
    @classmethod
    def _validate_source_record_id(cls, value: str | None) -> str | None:
        return validate_optional_text(
            value,
            field_name="source_record_id",
            max_length=SOURCE_RECORD_ID_MAX_LENGTH,
        )

    @field_validator("batch_id")
    @classmethod
    def _validate_batch_id(cls, value: str | None) -> str | None:
        return validate_optional_text(value, field_name="batch_id", max_length=BATCH_ID_MAX_LENGTH)

    @field_validator("extracted_at", "observed_at")
    @classmethod
    def _validate_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "timestamp must be timezone-aware"
            raise ValueError(msg)
        return value

"""Loadable raw record contract and deterministic identity helpers."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from felts.core.schemas.identifiers import (
    BATCH_ID_MAX_LENGTH,
    ENTITY_MAX_LENGTH,
    SCHEMA_NAME_MAX_LENGTH,
    SCHEMA_VERSION_MAX_LENGTH,
    SOURCE_MAX_LENGTH,
    SOURCE_RECORD_ID_MAX_LENGTH,
    validate_identifier,
    validate_optional_text,
)


class ValidationErrorDetail(BaseModel):
    """Normalized validation error persisted with invalid raw records."""

    model_config = ConfigDict(frozen=True)

    path: str
    message: str
    type: str


def canonical_payload_json(payload: dict[str, Any]) -> str:
    """Serialize payloads for stable identity without coercing values."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload_json(payload).encode("utf-8")).hexdigest()


def _timestamp_identity(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def make_raw_record_id(
    *,
    source: str,
    entity: str,
    payload: dict[str, Any],
    source_record_id: str | None = None,
    observed_at: datetime | None = None,
    extracted_at: datetime | None = None,
) -> str:
    """Derive deterministic raw identity for ingestion idempotency."""

    identity = {
        "source": source,
        "entity": entity,
        "payload_hash": canonical_payload_hash(payload),
        "source_record_id": source_record_id,
        "observed_at": _timestamp_identity(observed_at),
        "extracted_at": None,
    }
    if source_record_id is None and observed_at is None:
        identity["extracted_at"] = _timestamp_identity(extracted_at)
    identity_json = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(identity_json.encode("utf-8")).hexdigest()


class RawRecord(BaseModel):
    """A loadable raw record with ingestion metadata."""

    model_config = ConfigDict(frozen=True)

    id: str
    source: str
    entity: str
    payload: dict[str, Any]
    extracted_at: datetime
    loaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    batch_id: str
    source_record_id: str | None = None
    observed_at: datetime | None = None
    schema_name: str | None = None
    schema_version: str | None = None
    is_valid: bool
    validation_errors: list[ValidationErrorDetail] = Field(default_factory=list)

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
    def _validate_batch_id(cls, value: str) -> str:
        if not value:
            msg = "batch_id must not be empty"
            raise ValueError(msg)
        if len(value) > BATCH_ID_MAX_LENGTH:
            msg = f"batch_id must be at most {BATCH_ID_MAX_LENGTH} characters"
            raise ValueError(msg)
        return value

    @field_validator("schema_name")
    @classmethod
    def _validate_schema_name(cls, value: str | None) -> str | None:
        return validate_optional_text(
            value, field_name="schema_name", max_length=SCHEMA_NAME_MAX_LENGTH
        )

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str | None) -> str | None:
        return validate_optional_text(
            value,
            field_name="schema_version",
            max_length=SCHEMA_VERSION_MAX_LENGTH,
        )

    @field_validator("extracted_at", "observed_at", "loaded_at")
    @classmethod
    def _validate_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "timestamp must be timezone-aware"
            raise ValueError(msg)
        return value

"""Validation helpers for core Felts identifiers."""

import re
from typing import Final

IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9_]+$")

SOURCE_MAX_LENGTH: Final[int] = 64
ENTITY_MAX_LENGTH: Final[int] = 64
SOURCE_RECORD_ID_MAX_LENGTH: Final[int] = 512
BATCH_ID_MAX_LENGTH: Final[int] = 128
SCHEMA_NAME_MAX_LENGTH: Final[int] = 128
SCHEMA_VERSION_MAX_LENGTH: Final[int] = 64


def validate_identifier(value: str, *, field_name: str, max_length: int) -> str:
    if not value:
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    if len(value) > max_length:
        msg = f"{field_name} must be at most {max_length} characters"
        raise ValueError(msg)
    if not IDENTIFIER_PATTERN.fullmatch(value):
        msg = f"{field_name} must match ^[a-z0-9_]+$"
        raise ValueError(msg)
    return value


def validate_optional_text(value: str | None, *, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    if len(value) > max_length:
        msg = f"{field_name} must be at most {max_length} characters"
        raise ValueError(msg)
    return value

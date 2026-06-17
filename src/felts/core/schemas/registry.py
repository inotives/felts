"""Schema registry for optional source/entity validation."""

from dataclasses import dataclass

from pydantic import BaseModel

from felts.core.exceptions import ValidationSetupError
from felts.core.schemas.identifiers import (
    ENTITY_MAX_LENGTH,
    SCHEMA_NAME_MAX_LENGTH,
    SCHEMA_VERSION_MAX_LENGTH,
    SOURCE_MAX_LENGTH,
    validate_identifier,
    validate_optional_text,
)


@dataclass(frozen=True)
class RegisteredSchema:
    source: str
    entity: str
    model: type[BaseModel]
    schema_name: str
    schema_version: str


class SchemaRegistry:
    """Current-schema lookup keyed by source and entity."""

    def __init__(self) -> None:
        self._schemas: dict[tuple[str, str], RegisteredSchema] = {}

    def register(
        self,
        *,
        source: str,
        entity: str,
        model: type[BaseModel],
        schema_name: str,
        schema_version: str,
    ) -> None:
        source = validate_identifier(source, field_name="source", max_length=SOURCE_MAX_LENGTH)
        entity = validate_identifier(entity, field_name="entity", max_length=ENTITY_MAX_LENGTH)
        validate_optional_text(
            schema_name, field_name="schema_name", max_length=SCHEMA_NAME_MAX_LENGTH
        )
        validate_optional_text(
            schema_version,
            field_name="schema_version",
            max_length=SCHEMA_VERSION_MAX_LENGTH,
        )

        key = (source, entity)
        if key in self._schemas:
            msg = f"schema already registered for source={source!r}, entity={entity!r}"
            raise ValidationSetupError(msg)

        self._schemas[key] = RegisteredSchema(
            source=source,
            entity=entity,
            model=model,
            schema_name=schema_name,
            schema_version=schema_version,
        )

    def get(self, *, source: str, entity: str) -> RegisteredSchema | None:
        source = validate_identifier(source, field_name="source", max_length=SOURCE_MAX_LENGTH)
        entity = validate_identifier(entity, field_name="entity", max_length=ENTITY_MAX_LENGTH)
        return self._schemas.get((source, entity))

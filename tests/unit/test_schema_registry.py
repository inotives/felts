import pytest
from pydantic import BaseModel

from felts.core.exceptions import ValidationSetupError
from felts.core.schemas import SchemaRegistry


class ExamplePayload(BaseModel):
    price: float


def test_schema_registry_registers_and_retrieves_schema_metadata() -> None:
    registry = SchemaRegistry()

    registry.register(
        source="test_source",
        entity="prices",
        model=ExamplePayload,
        schema_name="test_source_prices",
        schema_version="1",
    )

    registered = registry.get(source="test_source", entity="prices")

    assert registered is not None
    assert registered.model is ExamplePayload
    assert registered.schema_name == "test_source_prices"
    assert registered.schema_version == "1"


def test_schema_registry_rejects_duplicate_registration() -> None:
    registry = SchemaRegistry()
    registry.register(
        source="test_source",
        entity="prices",
        model=ExamplePayload,
        schema_name="test_source_prices",
        schema_version="1",
    )

    with pytest.raises(ValidationSetupError):
        registry.register(
            source="test_source",
            entity="prices",
            model=ExamplePayload,
            schema_name="test_source_prices",
            schema_version="1",
        )

from collections.abc import Sequence

import pytest
from pydantic import BaseModel

from felts.core.exceptions import WriterInputError
from felts.core.loaders import LoadResult, RawWriter
from felts.core.schemas import ExtractedRecord, RawRecord, SchemaRegistry


class MemoryLoader:
    def __init__(self) -> None:
        self.chunks: list[list[RawRecord]] = []

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        chunk = list(records)
        self.chunks.append(chunk)
        return LoadResult(inserted_count=len(chunk))


class PricePayload(BaseModel):
    price: float


def test_raw_writer_lands_record_without_schema() -> None:
    loader = MemoryLoader()
    writer = RawWriter(schema_registry=SchemaRegistry(), loader=loader)

    result = writer.write(
        [ExtractedRecord(source="csv_import", entity="prices", payload={"price": "1.23"})],
        batch_id="batch-1",
    )

    assert result.batch_id == "batch-1"
    assert result.received_count == 1
    assert result.valid_count == 1
    assert result.loaded_count == 1
    assert loader.chunks[0][0].schema_name is None
    assert loader.chunks[0][0].validation_errors == []


def test_raw_writer_records_validation_errors_but_still_loads_invalid_record() -> None:
    registry = SchemaRegistry()
    registry.register(
        source="coingecko",
        entity="markets",
        model=PricePayload,
        schema_name="coingecko_markets",
        schema_version="1",
    )
    loader = MemoryLoader()
    writer = RawWriter(schema_registry=registry, loader=loader)

    result = writer.write(
        [ExtractedRecord(source="coingecko", entity="markets", payload={"price": "bad"})],
        batch_id="batch-1",
    )

    raw_record = loader.chunks[0][0]
    assert result.invalid_count == 1
    assert result.loaded_count == 1
    assert result.errors[0].stage == "validation"
    assert raw_record.is_valid is False
    assert raw_record.schema_name == "coingecko_markets"
    assert raw_record.schema_version == "1"
    assert raw_record.validation_errors[0].path == "price"


def test_raw_writer_chunks_iterable_records() -> None:
    loader = MemoryLoader()
    writer = RawWriter(
        schema_registry=SchemaRegistry(),
        loader=loader,
        loader_batch_size=2,
    )

    def records() -> Sequence[ExtractedRecord]:
        return [
            ExtractedRecord(source="csv_import", entity="prices", payload={"row": 1}),
            ExtractedRecord(source="csv_import", entity="prices", payload={"row": 2}),
            ExtractedRecord(source="csv_import", entity="prices", payload={"row": 3}),
        ]

    result = writer.write(iter(records()), batch_id="batch-1")

    assert [len(chunk) for chunk in loader.chunks] == [2, 1]
    assert result.received_count == 3
    assert result.loaded_count == 3


def test_raw_writer_rejects_conflicting_batch_id() -> None:
    writer = RawWriter(schema_registry=SchemaRegistry(), loader=MemoryLoader())

    with pytest.raises(WriterInputError):
        writer.write(
            [
                ExtractedRecord(
                    source="csv_import",
                    entity="prices",
                    payload={"row": 1},
                    batch_id="record-batch",
                )
            ],
            batch_id="writer-batch",
        )


def test_raw_writer_uses_record_level_batch_id_when_writer_batch_id_is_absent() -> None:
    loader = MemoryLoader()
    writer = RawWriter(schema_registry=SchemaRegistry(), loader=loader)

    result = writer.write(
        [
            ExtractedRecord(
                source="csv_import",
                entity="prices",
                payload={"row": 1},
                batch_id="record-batch",
            )
        ]
    )

    assert result.batch_id == "record-batch"
    assert loader.chunks[0][0].batch_id == "record-batch"

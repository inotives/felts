"""High-level raw writer."""

import logging
from collections.abc import Iterable
from itertools import islice
from uuid import uuid4

from pydantic import ValidationError

from felts.core.exceptions import WriterInputError
from felts.core.loaders.base import BaseLoader, LoadResult, ResultError, WriteResult
from felts.core.schemas import (
    ExtractedRecord,
    RawRecord,
    SchemaRegistry,
    ValidationErrorDetail,
    make_raw_record_id,
)

logger = logging.getLogger(__name__)


class RawWriter:
    """Convert extracted records into raw records and persist them."""

    def __init__(
        self,
        *,
        schema_registry: SchemaRegistry,
        loader: BaseLoader,
        loader_batch_size: int = 1000,
    ) -> None:
        if loader_batch_size < 1:
            msg = "loader_batch_size must be greater than zero"
            raise WriterInputError(msg)
        self.schema_registry = schema_registry
        self.loader = loader
        self.loader_batch_size = loader_batch_size

    def write(
        self, records: Iterable[ExtractedRecord], *, batch_id: str | None = None
    ) -> WriteResult:
        effective_batch_id = batch_id
        result: _MutableWriteResult | None = None
        iterator = iter(records)

        while chunk := list(islice(iterator, self.loader_batch_size)):
            if effective_batch_id is None:
                effective_batch_id = _resolve_batch_id(chunk)
            if result is None:
                result = _MutableWriteResult(batch_id=effective_batch_id)
            raw_records = [
                self._to_raw_record(record, batch_id=effective_batch_id, result=result)
                for record in chunk
            ]
            load_result = self.loader.write_records(raw_records)
            result.apply_load_result(load_result)

        if result is None:
            result = _MutableWriteResult(batch_id=effective_batch_id or uuid4().hex)

        return result.freeze()

    def _to_raw_record(
        self,
        record: ExtractedRecord,
        *,
        batch_id: str,
        result: "_MutableWriteResult",
    ) -> RawRecord:
        if record.batch_id is not None and record.batch_id != batch_id:
            msg = f"record batch_id {record.batch_id!r} conflicts with writer batch_id {batch_id!r}"
            raise WriterInputError(msg)

        result.received_count += 1
        registered_schema = self.schema_registry.get(source=record.source, entity=record.entity)
        validation_errors: list[ValidationErrorDetail] = []
        is_valid = True
        schema_name: str | None = None
        schema_version: str | None = None

        if registered_schema is not None:
            schema_name = registered_schema.schema_name
            schema_version = registered_schema.schema_version
            try:
                registered_schema.model.model_validate(record.payload)
            except ValidationError as exc:
                is_valid = False
                validation_errors = _normalize_validation_errors(exc)

        record_id = make_raw_record_id(
            source=record.source,
            entity=record.entity,
            source_record_id=record.source_record_id,
            observed_at=record.observed_at,
            extracted_at=record.extracted_at,
            payload=record.payload,
        )

        if is_valid:
            result.valid_count += 1
        else:
            result.invalid_count += 1
            result.errors.append(
                ResultError(
                    record_id=record_id,
                    source=record.source,
                    entity=record.entity,
                    stage="validation",
                    message="payload failed schema validation",
                    details=[error.model_dump() for error in validation_errors],
                )
            )

        return RawRecord(
            id=record_id,
            source=record.source,
            entity=record.entity,
            source_record_id=record.source_record_id,
            observed_at=record.observed_at,
            extracted_at=record.extracted_at,
            batch_id=batch_id,
            schema_name=schema_name,
            schema_version=schema_version,
            is_valid=is_valid,
            validation_errors=validation_errors,
            payload=record.payload,
        )


class _MutableWriteResult:
    def __init__(self, *, batch_id: str) -> None:
        self.batch_id = batch_id
        self.received_count = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.loaded_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.errors: list[ResultError] = []

    def apply_load_result(self, result: LoadResult) -> None:
        self.loaded_count += result.inserted_count
        self.skipped_count += result.skipped_count
        self.failed_count += result.failed_count
        self.errors.extend(result.errors)

    def freeze(self) -> WriteResult:
        return WriteResult(
            batch_id=self.batch_id,
            received_count=self.received_count,
            valid_count=self.valid_count,
            invalid_count=self.invalid_count,
            loaded_count=self.loaded_count,
            skipped_count=self.skipped_count,
            failed_count=self.failed_count,
            errors=self.errors,
        )


def _normalize_validation_errors(error: ValidationError) -> list[ValidationErrorDetail]:
    details: list[ValidationErrorDetail] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ()))
        details.append(
            ValidationErrorDetail(
                path=location,
                message=str(item.get("msg", "validation error")),
                type=str(item.get("type", "validation_error")),
            )
        )
    return details


def _resolve_batch_id(records: list[ExtractedRecord]) -> str:
    for record in records:
        if record.batch_id is not None:
            return record.batch_id
    return uuid4().hex

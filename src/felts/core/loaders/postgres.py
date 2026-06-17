"""Synchronous Postgres raw record loader."""

import logging
from collections.abc import Sequence
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from felts.core.loaders.base import LoadResult, ResultError
from felts.core.schemas import RawRecord

logger = logging.getLogger(__name__)


class PostgresRawLoader:
    """Persist raw records into a Postgres raw landing table."""

    def __init__(self, *, conninfo: str, schema: str = "raw", table: str = "raw_records") -> None:
        self.conninfo = conninfo
        self.schema = schema
        self.table = table

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        if not records:
            return LoadResult()

        insert_key_query = sql.SQL(
            """
            insert into {}.raw_record_keys (id)
            values (%(id)s)
            on conflict (id) do nothing
            returning id
            """
        ).format(sql.Identifier(self.schema))

        insert_record_query = sql.SQL(
            """
            insert into {}.{} (
                id,
                source,
                entity,
                source_record_id,
                observed_at,
                extracted_at,
                loaded_at,
                batch_id,
                schema_name,
                schema_version,
                is_valid,
                validation_errors,
                payload
            )
            values (
                %(id)s,
                %(source)s,
                %(entity)s,
                %(source_record_id)s,
                %(observed_at)s,
                %(extracted_at)s,
                %(loaded_at)s,
                %(batch_id)s,
                %(schema_name)s,
                %(schema_version)s,
                %(is_valid)s,
                %(validation_errors)s,
                %(payload)s
            )
            """
        ).format(sql.Identifier(self.schema), sql.Identifier(self.table))

        inserted_count = 0
        skipped_count = 0

        try:
            with psycopg.connect(self.conninfo) as connection:
                with connection.cursor() as cursor:
                    for record in records:
                        cursor.execute(insert_key_query, {"id": record.id})
                        inserted_id = cursor.fetchone()
                        if inserted_id is None:
                            skipped_count += 1
                        else:
                            cursor.execute(insert_record_query, self._to_row(record))
                            inserted_count += 1
        except psycopg.Error as exc:
            logger.exception("Postgres raw load failed")
            first_record = records[0]
            return LoadResult(
                failed_count=len(records),
                errors=[
                    ResultError(
                        record_id=first_record.id,
                        source=first_record.source,
                        entity=first_record.entity,
                        stage="load",
                        message=str(exc),
                    )
                ],
            )

        return LoadResult(inserted_count=inserted_count, skipped_count=skipped_count)

    @staticmethod
    def _to_row(record: RawRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "source": record.source,
            "entity": record.entity,
            "source_record_id": record.source_record_id,
            "observed_at": record.observed_at,
            "extracted_at": record.extracted_at,
            "loaded_at": record.loaded_at,
            "batch_id": record.batch_id,
            "schema_name": record.schema_name,
            "schema_version": record.schema_version,
            "is_valid": record.is_valid,
            "validation_errors": Jsonb([error.model_dump() for error in record.validation_errors]),
            "payload": Jsonb(record.payload),
        }

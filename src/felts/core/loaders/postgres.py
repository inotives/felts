"""Synchronous Postgres raw record loader."""

import logging
from collections import defaultdict
from collections.abc import Sequence
from hashlib import sha1
from typing import Any

import psycopg
from psycopg import Cursor, sql
from psycopg.types.json import Jsonb

from felts.core.loaders.base import LoadResult, ResultError
from felts.core.schemas import RawRecord

logger = logging.getLogger(__name__)


MAX_IDENTIFIER_LENGTH = 63


class PostgresRawLoader:
    """Persist raw records into source-schema/entity-table raw landing tables."""

    def __init__(self, *, conninfo: str, schema: str = "raw", table_prefix: str = "raw") -> None:
        self.conninfo = conninfo
        self.schema = schema
        self.table_prefix = table_prefix

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

        inserted_count = 0
        skipped_count = 0
        grouped_records = self._group_by_table(records)

        try:
            with psycopg.connect(self.conninfo) as connection:
                with connection.cursor() as cursor:
                    for (schema_name, table_name), table_records in grouped_records.items():
                        self._ensure_raw_table(
                            cursor,
                            schema_name=schema_name,
                            table_name=table_name,
                        )
                        insert_record_query = self._insert_record_query(
                            schema_name=schema_name,
                            table_name=table_name,
                        )
                        record_exists_query = self._record_exists_query(
                            schema_name=schema_name,
                            table_name=table_name,
                        )
                        for record in table_records:
                            cursor.execute(insert_key_query, {"id": record.id})
                            inserted_id = cursor.fetchone()
                            if inserted_id is None and self._record_exists(
                                cursor,
                                query=record_exists_query,
                                record=record,
                            ):
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

    def schema_name_for_record(self, record: RawRecord) -> str:
        return raw_source_schema_name(source=record.source)

    def table_name_for_record(self, record: RawRecord) -> str:
        return raw_entity_table_name(table_prefix=self.table_prefix, entity=record.entity)

    def _group_by_table(
        self, records: Sequence[RawRecord]
    ) -> dict[tuple[str, str], list[RawRecord]]:
        grouped: dict[tuple[str, str], list[RawRecord]] = defaultdict(list)
        for record in records:
            grouped[
                (self.schema_name_for_record(record), self.table_name_for_record(record))
            ].append(record)
        return grouped

    def _ensure_raw_table(self, cursor: Cursor[Any], *, schema_name: str, table_name: str) -> None:
        cursor.execute(
            sql.SQL("create schema if not exists {}").format(sql.Identifier(schema_name))
        )
        cursor.execute(
            sql.SQL(
                """
                create table if not exists {}.{} (
                    id text not null,
                    source text not null,
                    entity text not null,
                    source_record_id text,
                    observed_at timestamptz,
                    extracted_at timestamptz not null,
                    loaded_at timestamptz not null default now(),
                    batch_id text not null,
                    schema_name text,
                    schema_version text,
                    is_valid boolean not null,
                    validation_errors jsonb not null default '[]'::jsonb,
                    payload jsonb not null,
                    check (source ~ '^[a-z0-9_]+$'),
                    check (entity ~ '^[a-z0-9_]+$'),
                    check (jsonb_typeof(payload) = 'object'),
                    check (jsonb_typeof(validation_errors) = 'array')
                )
                """
            ).format(sql.Identifier(schema_name), sql.Identifier(table_name))
        )
        cursor.execute(
            "select create_hypertable(%s, 'extracted_at', if_not_exists => true)",
            [f"{schema_name}.{table_name}"],
        )
        cursor.execute(
            sql.SQL("create index if not exists {} on {}.{} (id)").format(
                sql.Identifier(_index_name(table_name=table_name, suffix="id_idx")),
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )
        )
        cursor.execute(
            sql.SQL(
                "create index if not exists {} on {}.{} (source, entity, extracted_at desc)"
            ).format(
                sql.Identifier(
                    _index_name(table_name=table_name, suffix="source_entity_extracted_at_idx")
                ),
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )
        )
        cursor.execute(
            sql.SQL("create index if not exists {} on {}.{} (batch_id)").format(
                sql.Identifier(_index_name(table_name=table_name, suffix="batch_id_idx")),
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )
        )

    def _insert_record_query(self, *, schema_name: str, table_name: str) -> sql.Composed:
        return sql.SQL(
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
        ).format(sql.Identifier(schema_name), sql.Identifier(table_name))

    def _record_exists_query(self, *, schema_name: str, table_name: str) -> sql.Composed:
        return sql.SQL("select 1 from {}.{} where id = %(id)s limit 1").format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
        )

    def _record_exists(
        self,
        cursor: Cursor[Any],
        *,
        query: sql.Composed,
        record: RawRecord,
    ) -> bool:
        cursor.execute(query, {"id": record.id})
        return cursor.fetchone() is not None

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


def raw_source_schema_name(*, source: str) -> str:
    return source


def raw_entity_table_name(*, table_prefix: str, entity: str) -> str:
    return f"{table_prefix}_{entity}"


def _index_name(*, table_name: str, suffix: str) -> str:
    name = f"{table_name}_{suffix}"
    if len(name) <= MAX_IDENTIFIER_LENGTH:
        return name
    digest = sha1(name.encode("utf-8")).hexdigest()[:8]
    keep = MAX_IDENTIFIER_LENGTH - len(digest) - 1
    return f"{name[:keep]}_{digest}"

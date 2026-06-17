from datetime import UTC, datetime

import psycopg
import pytest

from felts.config import Settings
from felts.core.loaders import PostgresRawLoader, postgres_loader_config_from_settings
from felts.core.schemas import RawRecord


def _postgres_available(conninfo: str) -> bool:
    try:
        with psycopg.connect(conninfo, connect_timeout=2):
            return True
    except psycopg.OperationalError:
        return False


def test_postgres_loader_writes_raw_record_and_skips_duplicate() -> None:
    settings = Settings()
    config = postgres_loader_config_from_settings(settings)
    if not _postgres_available(config.conninfo):
        pytest.skip("local Postgres is not available; run `make db-up`")

    loader = PostgresRawLoader(
        conninfo=config.conninfo,
        schema=config.schema,
        table=config.table,
    )
    record = RawRecord(
        id="integration-test-raw-record",
        source="csv_import",
        entity="prices",
        source_record_id="integration-test-1",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        extracted_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
        loaded_at=datetime(2026, 1, 1, 1, 1, tzinfo=UTC),
        batch_id="integration-test-batch",
        is_valid=True,
        payload={"price": 1},
    )

    first_result = loader.write_records([record])
    second_result = loader.write_records([record])

    assert first_result.inserted_count in {0, 1}
    assert second_result.skipped_count == 1

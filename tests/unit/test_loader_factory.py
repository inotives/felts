from felts.config import Settings
from felts.core.loaders import (
    PostgresRawLoader,
    create_loader,
    postgres_loader_config_from_settings,
)


def test_settings_raw_table_defaults() -> None:
    settings = Settings()

    assert settings.raw_schema == "raw"
    assert settings.raw_table == "raw_records"
    assert settings.raw_table_name == "raw.raw_records"
    assert settings.loader_batch_size == 1000


def test_loader_factory_translates_settings_to_loader_config() -> None:
    settings = Settings(
        FELTS_DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/db",
        FELTS_RAW_SCHEMA="raw_test",
        FELTS_RAW_TABLE="raw_records_test",
    )

    config = postgres_loader_config_from_settings(settings)
    loader = create_loader(settings)

    assert config.conninfo == "postgresql://user:pass@localhost:5432/db"
    assert config.schema == "raw_test"
    assert config.table == "raw_records_test"
    assert isinstance(loader, PostgresRawLoader)
    assert loader.schema == "raw_test"
    assert loader.table == "raw_records_test"

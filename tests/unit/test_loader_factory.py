from felts.config import Settings
from felts.core.loaders import (
    PostgresRawLoader,
    create_loader,
    postgres_loader_config_from_settings,
    raw_entity_table_name,
    raw_source_schema_name,
)


def test_settings_raw_table_defaults() -> None:
    settings = Settings()

    assert settings.raw_schema == "raw"
    assert settings.raw_table_prefix == "raw"
    assert settings.raw_table_name == "<source>.raw_<entity>"
    assert settings.loader_batch_size == 1000


def test_loader_factory_translates_settings_to_loader_config() -> None:
    settings = Settings(
        FELTS_DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/db",
        FELTS_RAW_SCHEMA="raw_test",
        FELTS_RAW_TABLE_PREFIX="landing",
    )

    config = postgres_loader_config_from_settings(settings)
    loader = create_loader(settings)

    assert config.conninfo == "postgresql://user:pass@localhost:5432/db"
    assert config.schema == "raw_test"
    assert config.table_prefix == "landing"
    assert isinstance(loader, PostgresRawLoader)
    assert loader.schema == "raw_test"
    assert loader.table_prefix == "landing"


def test_raw_physical_names_use_source_schema_entity_table_pattern() -> None:
    assert raw_source_schema_name(source="coingecko") == "coingecko"
    assert raw_entity_table_name(table_prefix="raw", entity="coins_markets") == "raw_coins_markets"

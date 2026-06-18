"""Loader factory functions."""

from dataclasses import dataclass
from typing import Literal

from felts.config import Settings
from felts.core.exceptions import ConfigurationError
from felts.core.loaders.postgres import PostgresRawLoader

LoaderName = Literal["postgres"]


@dataclass(frozen=True)
class PostgresLoaderConfig:
    conninfo: str
    schema: str
    table_prefix: str


def postgres_loader_config_from_settings(settings: Settings) -> PostgresLoaderConfig:
    if not settings.database_url:
        msg = "FELTS_DATABASE_URL is required for the Postgres loader"
        raise ConfigurationError(msg)
    return PostgresLoaderConfig(
        conninfo=_to_psycopg_conninfo(settings.database_url),
        schema=settings.raw_schema,
        table_prefix=settings.raw_table_prefix,
    )


def create_loader(settings: Settings, *, name: LoaderName = "postgres") -> PostgresRawLoader:
    if name != "postgres":
        msg = f"unsupported loader: {name}"
        raise ConfigurationError(msg)
    config = postgres_loader_config_from_settings(settings)
    return PostgresRawLoader(
        conninfo=config.conninfo,
        schema=config.schema,
        table_prefix=config.table_prefix,
    )


def _to_psycopg_conninfo(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url

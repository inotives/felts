import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_DIR = REPO_ROOT / "settings"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
        yaml_file=REPO_ROOT / "config.yaml",
        yaml_file_encoding="utf-8",
    )

    env: str = Field(default="local", alias="FELTS_ENV")

    db_host: str = Field(default="localhost", alias="FELTS_DB_HOST")
    db_port: int = Field(default=5432, alias="FELTS_DB_PORT")
    db_name: str = Field(default="felts", alias="FELTS_DB_NAME")
    db_user: str = Field(default="felts", alias="FELTS_DB_USER")
    db_password: str = Field(default="felts", alias="FELTS_DB_PASSWORD")
    database_url: str = Field(
        default="postgresql+psycopg://felts:felts@localhost:5432/felts",
        alias="FELTS_DATABASE_URL",
    )

    prefect_api_url: str = Field(default="http://127.0.0.1:4200/api", alias="PREFECT_API_URL")
    prefect_api_database_connection_url: str = Field(
        default="postgresql+asyncpg://prefect:prefect@localhost:5432/prefect",
        alias="PREFECT_API_DATABASE_CONNECTION_URL",
    )
    prefect_work_pool: str = Field(default="local", alias="FELTS_PREFECT_WORK_POOL")
    prefect_work_pool_type: str = Field(default="process", alias="FELTS_PREFECT_WORK_POOL_TYPE")
    prefect_work_queue: str = Field(default="default", alias="FELTS_PREFECT_WORK_QUEUE")

    dbt_project_dir: Path = Field(default=Path("transforms"), alias="FELTS_DBT_PROJECT_DIR")
    dbt_profiles_dir: Path = Field(default=Path("transforms"), alias="FELTS_DBT_PROFILES_DIR")
    dbt_command: str = Field(default="dbt", alias="FELTS_DBT_COMMAND")

    raw_schema: str = Field(default="raw", alias="FELTS_RAW_SCHEMA")
    raw_table_prefix: str = Field(default="raw", alias="FELTS_RAW_TABLE_PREFIX")
    loader_batch_size: int = Field(default=1000, alias="FELTS_LOADER_BATCH_SIZE")

    coingecko_api_key: str | None = Field(default=None, alias="COINGECKO_API_KEY")
    coingecko_base_url: str = Field(
        default="https://api.coingecko.com/api/v3", alias="COINGECKO_BASE_URL"
    )
    coingecko_request_timeout_seconds: int = Field(
        default=30, gt=0, alias="COINGECKO_REQUEST_TIMEOUT_SECONDS"
    )
    coingecko_retry_max_attempts: int = Field(default=3, ge=1, alias="COINGECKO_RETRY_MAX_ATTEMPTS")
    coingecko_markets_vs_currency: str = Field(
        default="usd", min_length=1, alias="COINGECKO_MARKETS_VS_CURRENCY"
    )
    coingecko_markets_per_page: int = Field(default=250, gt=0, alias="COINGECKO_MARKETS_PER_PAGE")
    coingecko_markets_max_pages: int = Field(default=1, ge=1, alias="COINGECKO_MARKETS_MAX_PAGES")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            DotEnvSettingsSource(
                settings_cls,
                env_file=settings_env_file(),
                env_file_encoding="utf-8",
            ),
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @property
    def raw_table_name(self) -> str:
        return f"<source>.{self.raw_table_prefix}_<entity>"

    def resolve_project_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return REPO_ROOT / path

    @property
    def resolved_dbt_project_dir(self) -> Path:
        return self.resolve_project_path(self.dbt_project_dir)

    @property
    def resolved_dbt_profiles_dir(self) -> Path:
        return self.resolve_project_path(self.dbt_profiles_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def settings_env_file(env: str | None = None) -> Path:
    selected_env = env or os.environ.get("FELTS_ENV") or "local"
    return SETTINGS_DIR / f".env.{selected_env}"

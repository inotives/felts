from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
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

    dbt_project_dir: Path = Field(default=Path("transforms"), alias="FELTS_DBT_PROJECT_DIR")
    dbt_profiles_dir: Path = Field(default=Path("transforms"), alias="FELTS_DBT_PROFILES_DIR")

    coingecko_api_key: str | None = Field(default=None, alias="COINGECKO_API_KEY")

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

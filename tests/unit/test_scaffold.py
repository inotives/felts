from pathlib import Path

from pytest import MonkeyPatch

import felts
from felts.config import Settings, get_settings


def test_package_imports() -> None:
    assert felts.__version__


def test_settings_resolve_dbt_project_dir() -> None:
    settings = get_settings()

    assert settings.resolved_dbt_project_dir == Path.cwd() / "transforms"


def test_settings_load_project_defaults_from_yaml() -> None:
    settings = Settings(_env_file=None)

    assert settings.prefect_work_pool == "local"
    assert settings.dbt_command == "dbt"


def test_environment_overrides_project_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FELTS_PREFECT_WORK_POOL", "override-pool")

    settings = Settings(_env_file=None)

    assert settings.prefect_work_pool == "override-pool"

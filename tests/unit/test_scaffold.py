from pathlib import Path

from pytest import MonkeyPatch

import felts
from felts.config import Settings, get_settings
from felts.config import settings as settings_module


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


def test_settings_loads_default_local_env_file(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FELTS_ENV", raising=False)
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", tmp_path)
    (tmp_path / ".env.local").write_text("FELTS_PREFECT_WORK_POOL=local-file\n")

    settings = Settings()

    assert settings.prefect_work_pool == "local-file"


def test_settings_selects_env_specific_file(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FELTS_ENV", "dev")
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", tmp_path)
    (tmp_path / ".env.dev").write_text("FELTS_PREFECT_WORK_POOL=dev-file\n")

    settings = Settings()

    assert settings.env == "dev"
    assert settings.prefect_work_pool == "dev-file"
    assert settings_module.settings_env_file() == tmp_path / ".env.dev"

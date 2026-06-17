from pathlib import Path

import felts
from felts.config import get_settings


def test_package_imports() -> None:
    assert felts.__version__


def test_settings_resolve_dbt_project_dir() -> None:
    settings = get_settings()

    assert settings.resolved_dbt_project_dir == Path.cwd() / "transforms"

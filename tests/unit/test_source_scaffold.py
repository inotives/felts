import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

SCAFFOLD_PATH = Path(__file__).parents[2] / "scripts" / "scaffold.py"
SCAFFOLD_SPEC = importlib.util.spec_from_file_location("felts_scaffold", SCAFFOLD_PATH)
assert SCAFFOLD_SPEC is not None and SCAFFOLD_SPEC.loader is not None
scaffold = importlib.util.module_from_spec(SCAFFOLD_SPEC)
sys.modules[SCAFFOLD_SPEC.name] = scaffold
SCAFFOLD_SPEC.loader.exec_module(scaffold)

EntitySpec = scaffold.EntitySpec
ScaffoldError = scaffold.ScaffoldError
scaffold_entity = scaffold.scaffold_entity
scaffold_source = scaffold.scaffold_source


def _repo(tmp_path: Path) -> Path:
    root = tmp_path
    cli = root / "src" / "felts" / "cli.py"
    orchestrator = root / "src" / "felts" / "schedules" / "orchestrator.py"
    cli.parent.mkdir(parents=True)
    orchestrator.parent.mkdir(parents=True)
    cli.write_text(
        "# scaffold: source-cli-imports:start\n"
        "# scaffold: source-cli-imports:end\n"
        "def parser():\n"
        "    # scaffold: source-cli-registrations:start\n"
        "    # scaffold: source-cli-registrations:end\n"
    )
    orchestrator.write_text(
        "# scaffold: source-orchestrator-imports:start\n"
        "# scaffold: source-orchestrator-imports:end\n"
        "def triggers():\n"
        "    # scaffold: source-transform-triggers:start\n"
        "    # scaffold: source-transform-triggers:end\n"
        "def deployments():\n"
        "    # scaffold: source-deployments:start\n"
        "    # scaffold: source-deployments:end\n"
    )
    return root


def _entity(source: str = "example") -> Any:
    return EntitySpec(
        source=source,
        entity="daily_prices",
        path="/query",
        response_shape="keyed_object",
        records_path="Time Series (Daily)",
        key_field="trading_date",
        id_fields=("symbol", "trading_date"),
        params=(("function", "TIME_SERIES_DAILY"),),
        runtime_params=("symbol",),
    )


def test_source_and_entity_scaffold_generate_explicit_feature(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    scaffold_source(root, "example", "https://api.example.test", run_checks=False)
    scaffold_entity(root, _entity(), run_checks=False)

    package = root / "src" / "felts" / "sources" / "example"
    assert (package / "extractor.py").exists()
    assert '"daily_prices": Endpoint(' in (package / "constants.py").read_text()
    assert "DailyPricesPayload" in (package / "schemas.py").read_text()
    assert "register_example_cli" in (root / "src" / "felts" / "cli.py").read_text()
    assert (
        "deploy_example_flows"
        in (root / "src" / "felts" / "schedules" / "orchestrator.py").read_text()
    )
    assert (
        root / "transforms" / "models" / "staging" / "example" / "stg_example__daily_prices.sql"
    ).exists()


def test_existing_source_is_not_overwritten(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    scaffold_source(root, "example", "https://api.example.test", run_checks=False)
    existing = root / "src" / "felts" / "sources" / "example" / "constants.py"
    before = existing.read_text()

    with pytest.raises(ScaffoldError, match="use the entity command"):
        scaffold_source(root, "example", "https://changed.example.test", run_checks=False)

    assert existing.read_text() == before


def test_entity_collision_leaves_source_unchanged(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    scaffold_source(root, "example", "https://api.example.test", run_checks=False)
    scaffold_entity(root, _entity(), run_checks=False)
    constants = root / "src" / "felts" / "sources" / "example" / "constants.py"
    before = constants.read_text()

    with pytest.raises(ScaffoldError, match="managed block collision"):
        scaffold_entity(root, _entity(), run_checks=False)

    assert constants.read_text() == before


def test_keyed_object_requires_records_path_and_key_field(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    scaffold_source(root, "example", "https://api.example.test", run_checks=False)
    invalid = EntitySpec(
        source="example",
        entity="daily_prices",
        path="/query",
        response_shape="keyed_object",
        records_path=None,
        key_field=None,
        id_fields=(),
        params=(),
        runtime_params=(),
    )

    with pytest.raises(ScaffoldError, match="requires --records-path"):
        scaffold_entity(root, invalid, run_checks=False)


def test_validation_failure_rolls_back_all_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo(tmp_path)
    cli = root / "src" / "felts" / "cli.py"
    orchestrator = root / "src" / "felts" / "schedules" / "orchestrator.py"
    before = (cli.read_text(), orchestrator.read_text())

    def fail_checks(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("validation failed")

    monkeypatch.setattr(scaffold, "_run_fast_checks", fail_checks)

    with pytest.raises(RuntimeError, match="validation failed"):
        scaffold_source(root, "example", "https://api.example.test")

    assert not (root / "src" / "felts" / "sources" / "example").exists()
    assert (cli.read_text(), orchestrator.read_text()) == before

#!/usr/bin/env python3
"""Generate explicit REST source and entity feature folders."""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
RESPONSE_SHAPES = ("list", "object", "data_object", "keyed_object")


class ScaffoldError(RuntimeError):
    """A user-correctable scaffold failure."""


@dataclass(frozen=True)
class EntitySpec:
    source: str
    entity: str
    path: str
    response_shape: str
    records_path: str | None
    key_field: str | None
    id_fields: tuple[str, ...]
    params: tuple[tuple[str, str], ...]
    runtime_params: tuple[str, ...]


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "source":
            scaffold_source(REPO_ROOT, args.source, args.base_url)
        else:
            scaffold_entity(
                REPO_ROOT,
                EntitySpec(
                    source=args.source,
                    entity=args.entity,
                    path=args.path,
                    response_shape=args.response_shape,
                    records_path=args.records_path,
                    key_field=args.key_field,
                    id_fields=tuple(args.id_field),
                    params=tuple(_parse_param(value) for value in args.param),
                    runtime_params=tuple(args.runtime_param),
                ),
            )
    except ScaffoldError as exc:
        parser.error(str(exc))
    return 0


def scaffold_source(
    root: Path,
    source: str,
    base_url: str,
    *,
    run_checks: bool = True,
) -> None:
    _validate_identifier("source", source)
    _validate_base_url(base_url)
    source_dir = root / "src" / "felts" / "sources" / source
    if source_dir.exists():
        raise ScaffoldError(f"source folder already exists: {source_dir}; use the entity command")

    writes = _source_files(root, source, base_url)
    writes.update(_source_registrations(root, source))
    _apply_transaction(
        root,
        writes,
        generated_python=_python_paths(writes),
        test_path=root / "tests" / "unit" / "sources" / source,
        run_checks=run_checks,
    )
    _print_source_next_steps(source)


def scaffold_entity(
    root: Path,
    spec: EntitySpec,
    *,
    run_checks: bool = True,
) -> None:
    _validate_entity_spec(spec)
    source_dir = root / "src" / "felts" / "sources" / spec.source
    if not source_dir.is_dir():
        raise ScaffoldError(
            f"source folder does not exist: {source_dir}; run the source command first"
        )

    writes = _entity_files(root, spec)
    _apply_transaction(
        root,
        writes,
        generated_python=_python_paths(writes),
        test_path=root / "tests" / "unit" / "sources" / spec.source,
        run_checks=run_checks,
    )
    _print_entity_next_steps(spec)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scripts/scaffold.py")
    commands = parser.add_subparsers(dest="command", required=True)

    source = commands.add_parser("source")
    source.add_argument("source")
    source.add_argument("--base-url", required=True)

    entity = commands.add_parser("entity")
    entity.add_argument("source")
    entity.add_argument("entity")
    entity.add_argument("--path", required=True)
    entity.add_argument("--response-shape", choices=RESPONSE_SHAPES, required=True)
    entity.add_argument("--records-path")
    entity.add_argument("--key-field")
    entity.add_argument("--id-field", action="append", default=[])
    entity.add_argument("--param", action="append", default=[])
    entity.add_argument("--runtime-param", action="append", default=[])
    return parser


def _source_files(root: Path, source: str, base_url: str) -> dict[Path, str]:
    package = root / "src" / "felts" / "sources" / source
    tests = root / "tests" / "unit" / "sources" / source
    source_title = _title(source)
    return {
        package / "__init__.py": (
            f'"""{source_title} source integration."""\n\n'
            f"from felts.sources.{source}.runner import run_{source}_source\n\n"
            f'__all__ = ["run_{source}_source"]\n'
        ),
        package / "constants.py": _constants_template(source, base_url),
        package / "schemas.py": _schemas_template(source),
        package / "extractor.py": _extractor_template(source),
        package / "runner.py": _runner_template(source),
        package / "events.py": _events_template(source),
        package / "flow.py": _flow_template(source),
        package / "deployments.py": _deployments_template(source),
        package / "automations.py": _automations_template(source),
        package / "cli.py": _cli_template(source),
        tests / "__init__.py": "",
        tests / "test_generated.py": _generated_test_template(source, base_url),
    }


def _source_registrations(root: Path, source: str) -> dict[Path, str]:
    cli_path = root / "src" / "felts" / "cli.py"
    orchestrator_path = root / "src" / "felts" / "schedules" / "orchestrator.py"
    cli = _read_required(cli_path)
    orchestrator = _read_required(orchestrator_path)
    cli = _append_managed_line(
        cli,
        "source-cli-imports",
        f"from felts.sources.{source}.cli import register_cli as register_{source}_cli",
    )
    cli = _append_managed_line(
        cli,
        "source-cli-registrations",
        f"    register_{source}_cli(subparsers)",
    )
    orchestrator = _append_managed_line(
        orchestrator,
        "source-orchestrator-imports",
        (
            f"from felts.sources.{source}.automations import "
            f"build_transform_triggers as {source}_triggers\n"
            f"from felts.sources.{source}.deployments import "
            f"deploy_source_flows as deploy_{source}_flows"
        ),
    )
    orchestrator = _append_managed_line(
        orchestrator,
        "source-transform-triggers",
        f"    triggers.extend({source}_triggers())",
    )
    orchestrator = _append_managed_line(
        orchestrator,
        "source-deployments",
        f"    registered.extend(deploy_{source}_flows(settings))",
    )
    return {cli_path: cli, orchestrator_path: orchestrator}


def _entity_files(root: Path, spec: EntitySpec) -> dict[Path, str]:
    package = root / "src" / "felts" / "sources" / spec.source
    tests = root / "tests" / "unit" / "sources" / spec.source
    writes: dict[Path, str] = {}

    constants_path = package / "constants.py"
    constants = _read_required(constants_path)
    constants = _append_managed_line(constants, "entities", f'    "{spec.entity}",')
    constants = _append_managed_line(
        constants,
        "endpoints",
        f'    "{spec.entity}": Endpoint(\n'
        f"        path={spec.path!r},\n"
        f"        response_shape={spec.response_shape!r},\n"
        f"        records_path={spec.records_path!r},\n"
        f"        key_field={spec.key_field!r},\n"
        f"        id_fields={spec.id_fields!r},\n"
        f"        params={dict(spec.params)!r},\n"
        f"        runtime_params={spec.runtime_params!r},\n"
        "    ),",
    )
    writes[constants_path] = constants

    schemas_path = package / "schemas.py"
    schema_fields = "\n".join(f"    {field}: Any" for field in spec.id_fields)
    schema_fields = f"\n{schema_fields}" if schema_fields else ""
    schemas = _append_managed_line(
        _read_required(schemas_path),
        "schemas",
        (
            f"class {_class_name(spec.entity)}Payload({_class_name(spec.source)}Model):"
            f"{schema_fields}\n    pass"
        ),
    )
    writes[schemas_path] = schemas

    runner_path = package / "runner.py"
    runner = _append_managed_line(
        _read_required(runner_path),
        "schema-imports",
        (f"from felts.sources.{spec.source}.schemas import {_class_name(spec.entity)}Payload"),
    )
    runner = _append_managed_line(
        runner,
        "schema-registrations",
        f'        "{spec.entity}": {_class_name(spec.entity)}Payload,',
    )
    writes[runner_path] = runner

    test_path = tests / "test_generated.py"
    tests_text = _append_managed_line(
        _read_required(test_path),
        "entity-tests",
        _entity_test(spec),
    )
    writes[test_path] = tests_text

    source_yml = root / "transforms" / "models" / "sources" / f"{spec.source}.yml"
    source_yml_content = (
        _read_required(source_yml)
        if source_yml.exists()
        else (
            "version: 2\n\n"
            "sources:\n"
            f"  - name: {spec.source}\n"
            f"    description: {_title(spec.source)} raw landing schema.\n"
            f"    schema: {spec.source}\n"
            "    tables:\n"
            "      # scaffold: dbt-source-tables:start\n"
            "      # scaffold: dbt-source-tables:end\n"
        )
    )
    writes[source_yml] = _append_managed_line(
        source_yml_content,
        "dbt-source-tables",
        (
            f"      - name: raw_{spec.entity}\n"
            f"        description: Raw {_title(spec.source)} "
            f"{spec.entity.replace('_', ' ')} records."
        ),
    )

    staging_dir = root / "transforms" / "models" / "staging" / spec.source
    model_yml = staging_dir / f"_{spec.source}__models.yml"
    model_yml_content = (
        _read_required(model_yml)
        if model_yml.exists()
        else (
            "version: 2\n\n"
            "models:\n"
            "  # scaffold: dbt-staging-models:start\n"
            "  # scaffold: dbt-staging-models:end\n"
        )
    )
    writes[model_yml] = _append_managed_line(
        model_yml_content,
        "dbt-staging-models",
        (
            f"  - name: stg_{spec.source}__{spec.entity}\n"
            "    description: >-\n"
            "      TODO(scaffold): select analytical fields, types, tests, and "
            "document the declared grain.\n"
            "    columns:\n"
            "      - name: raw_record_id\n"
            "        tests:\n"
            "          - not_null"
        ),
    )
    staging_sql = staging_dir / f"stg_{spec.source}__{spec.entity}.sql"
    if staging_sql.exists():
        raise ScaffoldError(f"target file already exists: {staging_sql}")
    writes[staging_sql] = _staging_sql(spec)
    return writes


def _constants_template(source: str, base_url: str) -> str:
    return f'''"""Generated {_title(source)} source constants."""

from dataclasses import dataclass
from typing import Literal

{source.upper()}_SOURCE = {source!r}
{source.upper()}_BASE_URL = {base_url!r}

ResponseShape = Literal["list", "object", "data_object", "keyed_object"]


@dataclass(frozen=True)
class Endpoint:
    path: str
    response_shape: ResponseShape
    records_path: str | None = None
    key_field: str | None = None
    id_fields: tuple[str, ...] = ()
    params: dict[str, str] | None = None
    runtime_params: tuple[str, ...] = ()


SUPPORTED_ENTITIES: tuple[str, ...] = (
    # scaffold: entities:start
    # scaffold: entities:end
)

ENDPOINTS: dict[str, Endpoint] = {{
    # scaffold: endpoints:start
    # scaffold: endpoints:end
}}

DBT_SELECTORS = {{
    entity: f"stg_{source}__{{entity}}+" for entity in SUPPORTED_ENTITIES
}}
'''


def _schemas_template(source: str) -> str:
    return f'''"""Generated permissive {_title(source)} payload schemas."""

from typing import Any  # noqa: F401

from pydantic import BaseModel, ConfigDict


class {_class_name(source)}Model(BaseModel):
    model_config = ConfigDict(extra="allow")


# scaffold: schemas:start
# scaffold: schemas:end
'''


def _extractor_template(source: str) -> str:
    prefix = source.upper()
    class_name = _class_name(source)
    return f'''"""Generated {_title(source)} REST extractor."""

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from itertools import product
from typing import Any

from felts.core.exceptions import ExtractionError
from felts.core.extractors.base import BaseExtractor
from felts.core.extractors.rest import RestClient
from felts.core.schemas import ExtractedRecord
from felts.sources.{source}.constants import {prefix}_SOURCE, ENDPOINTS, Endpoint


class {class_name}Extractor(BaseExtractor):
    def __init__(self, *, client: RestClient) -> None:
        self.client = client

    def extract(self) -> Iterable[ExtractedRecord]:
        for entity in ENDPOINTS:
            yield from self.extract_entity(entity)

    def extract_entity(
        self,
        entity: str,
        *,
        runtime_params: Mapping[str, Sequence[str]] | None = None,
    ) -> list[ExtractedRecord]:
        try:
            endpoint = ENDPOINTS[entity]
        except KeyError as exc:
            raise ExtractionError(f"unsupported {_title(source)} entity: {{entity}}") from exc
        runtime_params = runtime_params or {{}}
        missing = [name for name in endpoint.runtime_params if not runtime_params.get(name)]
        if missing:
            raise ExtractionError(
                f"missing runtime parameter(s) for {{entity}}: {{', '.join(missing)}}"
            )
        names = endpoint.runtime_params
        values = [runtime_params[name] for name in names]
        combinations = product(*values) if values else [()]
        records: list[ExtractedRecord] = []
        for combination in combinations:
            runtime_values = dict(zip(names, combination, strict=True))
            params = {{**(endpoint.params or {{}}), **runtime_values}}
            data = self.client.get_json(endpoint.path, params=params)
            records.extend(
                _records_from_response(
                    entity=entity,
                    endpoint=endpoint,
                    data=data,
                    runtime_values=runtime_values,
                )
            )
        return records


def _records_from_response(
    *,
    entity: str,
    endpoint: Endpoint,
    data: Any,
    runtime_values: Mapping[str, str],
) -> list[ExtractedRecord]:
    if endpoint.response_shape == "list":
        if not isinstance(data, list):
            raise ExtractionError(f"{{entity}} response must be a list")
        payloads = [_object(entity, item) for item in data]
    elif endpoint.response_shape == "object":
        payloads = [_object(entity, data)]
    elif endpoint.response_shape == "data_object":
        top_level = _object(entity, data)
        payloads = [_object(entity, top_level.get("data"))]
    else:
        top_level = _object(entity, data)
        selected: Any = top_level
        for part in (endpoint.records_path or "").split("."):
            if not isinstance(selected, dict) or part not in selected:
                raise ExtractionError(
                    f"{{entity}} response is missing records path {{endpoint.records_path!r}}"
                )
            selected = selected[part]
        if not isinstance(selected, dict):
            raise ExtractionError(f"{{entity}} keyed response must select an object")
        payloads = []
        for key, value in selected.items():
            payload = _object(entity, value)
            payload[endpoint.key_field or "key"] = key
            payloads.append(payload)

    records = []
    for payload in payloads:
        payload.update(runtime_values)
        records.append(
            ExtractedRecord(
                source={prefix}_SOURCE,
                entity=entity,
                payload=payload,
                source_record_id=_source_record_id(endpoint, payload),
            )
        )
    return records


def _source_record_id(endpoint: Endpoint, payload: Mapping[str, Any]) -> str | None:
    if not endpoint.id_fields:
        return None
    values = [payload.get(field) for field in endpoint.id_fields]
    if any(value is None for value in values):
        return None
    encoded = json.dumps(values, separators=(",", ":"), sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _object(entity: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExtractionError(f"{{entity}} response item must be an object")
    return dict(value)
'''


def _runner_template(source: str) -> str:
    prefix = source.upper()
    class_name = _class_name(source)
    return f'''"""Generated {_title(source)} source runner."""

# ruff: noqa: I001

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from pydantic import BaseModel

from felts.config import Settings, get_settings
from felts.core.extractors.rest import RestClient
from felts.core.loaders import RawWriter, create_loader
from felts.core.schemas import SchemaRegistry
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.{source}.constants import (
    {prefix}_BASE_URL,
    {prefix}_SOURCE,
    SUPPORTED_ENTITIES,
)
from felts.sources.{source}.extractor import {class_name}Extractor
# scaffold: schema-imports:start
# scaffold: schema-imports:end

SCHEMA_VERSION = "1"


def build_{source}_schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registrations: dict[str, type[BaseModel]] = {{
        # scaffold: schema-registrations:start
        # scaffold: schema-registrations:end
    }}
    for entity, model in registrations.items():
        registry.register(
            source={prefix}_SOURCE,
            entity=entity,
            model=model,
            schema_name=f"{source}_{{entity}}",
            schema_version=SCHEMA_VERSION,
        )
    return registry


def run_{source}_source(
    *,
    entities: Sequence[str] | None = None,
    runtime_params: Mapping[str, Sequence[str]] | None = None,
    settings: Settings | None = None,
    extractor: {class_name}Extractor | None = None,
    writer: RawWriter | None = None,
) -> SourceRunSummary:
    started_at = datetime.now(UTC)
    settings = settings or get_settings()
    selected = tuple(entities) if entities is not None else SUPPORTED_ENTITIES
    unsupported = set(selected) - set(SUPPORTED_ENTITIES)
    if unsupported:
        raise ValueError(f"unsupported {_title(source)} entities: {{sorted(unsupported)}}")

    owns_client = extractor is None
    client = None
    if extractor is None:
        client = _build_rest_client(settings)
        extractor = {class_name}Extractor(client=client)
    if writer is None:
        writer = RawWriter(
            schema_registry=build_{source}_schema_registry(),
            loader=create_loader(settings),
            loader_batch_size=settings.loader_batch_size,
        )

    summaries = []
    try:
        for entity in selected:
            records = extractor.extract_entity(entity, runtime_params=runtime_params)
            result = writer.write(records)
            summaries.append(EntityRunSummary.from_write_result(entity=entity, result=result))
    finally:
        if owns_client and client is not None:
            client.close()
    return SourceRunSummary(
        source={prefix}_SOURCE,
        started_at=started_at,
        ended_at=datetime.now(UTC),
        entities=tuple(summaries),
    )


def _build_rest_client(_settings: Settings) -> RestClient:
    # TODO(scaffold): add typed settings and request credentials when required.
    return RestClient(base_url={prefix}_BASE_URL)
'''


def _events_template(source: str) -> str:
    prefix = source.upper()
    return f'''"""Generated {_title(source)} Prefect event helpers."""

from typing import Any

from prefect.events import emit_event

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.{source}.constants import {prefix}_SOURCE, DBT_SELECTORS


def raw_completion_event_name(entity: str) -> str:
    return f"felts.raw.{{{prefix}_SOURCE}}.{{entity}}.completed"


def raw_completion_resource_id(entity: str) -> str:
    return f"felts.raw.{{{prefix}_SOURCE}}.{{entity}}"


def raw_completion_payload(summary: EntityRunSummary) -> dict[str, Any]:
    return {{
        "source": {prefix}_SOURCE,
        "entity": summary.entity,
        "batch_id": summary.batch_id,
        "inserted_count": summary.inserted_count,
        "skipped_count": summary.skipped_duplicate_count,
        "extracted_count": summary.extracted_count,
        "failed_count": summary.failed_count,
        "dbt_selector": DBT_SELECTORS[summary.entity],
    }}


def emit_raw_completion_events(summary: SourceRunSummary) -> list[str]:
    emitted = []
    for entity in summary.entities:
        if entity.inserted_count <= 0 or entity.failed_count:
            continue
        event_name = raw_completion_event_name(entity.entity)
        emit_event(
            event=event_name,
            resource={{
                "prefect.resource.id": raw_completion_resource_id(entity.entity),
                "felts.source": {prefix}_SOURCE,
                "felts.entity": entity.entity,
            }},
            payload=raw_completion_payload(entity),
        )
        emitted.append(event_name)
    return emitted
'''


def _flow_template(source: str) -> str:
    return f'''"""Generated {_title(source)} Prefect source flow."""

from collections.abc import Mapping, Sequence

from prefect import flow

from felts.core.sources import SourceRunSummary
from felts.sources.{source}.events import emit_raw_completion_events
from felts.sources.{source}.runner import run_{source}_source


@flow(name="{source}-source", retries=2, retry_delay_seconds=60)
def {source}_source_flow(
    entities: Sequence[str],
    runtime_params: Mapping[str, Sequence[str]],
) -> SourceRunSummary:
    summary = run_{source}_source(
        entities=entities,
        runtime_params=runtime_params,
    )
    emit_raw_completion_events(summary)
    return summary
'''


def _deployments_template(source: str) -> str:
    return f'''"""Generated manual {_title(source)} deployment definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from prefect.deployments.runner import RunnerDeployment

from felts.config import Settings
from felts.sources.{source}.constants import ENDPOINTS
from felts.sources.{source}.flow import {source}_source_flow


@dataclass(frozen=True)
class SourceDeploymentSpec:
    name: str
    entity: str

    @property
    def parameters(self) -> dict[str, object]:
        endpoint = ENDPOINTS[self.entity]
        return {{
            "entities": [self.entity],
            "runtime_params": {{name: [] for name in endpoint.runtime_params}},
        }}


def build_source_deployment_specs() -> tuple[SourceDeploymentSpec, ...]:
    return tuple(
        SourceDeploymentSpec(
            name=f"{source}-{{entity.replace('_', '-')}}-source",
            entity=entity,
        )
        for entity in ENDPOINTS
    )


def deploy_source_flows(settings: Settings) -> list[str]:
    names = []
    for spec in build_source_deployment_specs():
        deployment = cast(
            RunnerDeployment,
            {source}_source_flow.to_deployment(
                name=spec.name,
                work_pool_name=settings.prefect_work_pool,
                work_queue_name=settings.prefect_work_queue,
                schedules=None,
                parameters=spec.parameters,
                job_variables={{
                    "working_dir": str(settings.resolve_project_path(Path(".")))
                }},
                tags=["{source}", "source", spec.entity],
                description=(
                    "TODO(scaffold): provide required runtime parameters before "
                    f"registering {{spec.entity}}."
                ),
            ),
        )
        deployment.apply(work_pool_name=settings.prefect_work_pool)
        names.append(spec.name)
    return names
'''


def _automations_template(source: str) -> str:
    return f'''"""Generated {_title(source)} event-to-transform triggers."""

from prefect.events import DeploymentEventTrigger, DeploymentTriggerTypes, TriggerTypes

from felts.sources.{source}.constants import DBT_SELECTORS, SUPPORTED_ENTITIES
from felts.sources.{source}.events import raw_completion_event_name, raw_completion_resource_id


def build_transform_triggers() -> list[DeploymentTriggerTypes | TriggerTypes]:
    return [
        DeploymentEventTrigger(
            name=f"{source}-{{entity.replace('_', '-')}}-raw-completed-to-dbt-transform",
            expect={{raw_completion_event_name(entity)}},
            match={{"prefect.resource.id": raw_completion_resource_id(entity)}},
            parameters={{"selector": DBT_SELECTORS[entity], "run_tests": True}},
        )
        for entity in SUPPORTED_ENTITIES
    ]
'''


def _cli_template(source: str) -> str:
    return f'''"""Generated {_title(source)} CLI entrypoints."""

import argparse
from collections.abc import Sequence
from typing import Any

from felts.sources.{source}.constants import ENDPOINTS
from felts.sources.{source}.runner import run_{source}_source


def main(argv: Sequence[str] | None = None) -> int:
    from felts.cli import main as felts_main

    return felts_main(argv)


def register_cli(subparsers: Any) -> None:
    source = subparsers.add_parser("{source}")
    entities = source.add_subparsers(dest="{source}_entity")
    for entity, endpoint in ENDPOINTS.items():
        command = entities.add_parser(entity.replace("_", "-"))
        for name in endpoint.runtime_params:
            command.add_argument(f"--{{name.replace('_', '-')}}", action="append", required=True)
        command.set_defaults(handler=_run, entity=entity)


def _run(args: argparse.Namespace) -> int:
    endpoint = ENDPOINTS[args.entity]
    runtime_params = {{
        name: getattr(args, name) for name in endpoint.runtime_params
    }}
    summary = run_{source}_source(
        entities=[args.entity],
        runtime_params=runtime_params,
    )
    entity = summary.entities[0]
    print(
        f"source={{summary.source}} entity={{entity.entity}} "
        f"extracted={{entity.extracted_count}} inserted={{entity.inserted_count}} "
        f"skipped_duplicate={{entity.skipped_duplicate_count}} "
        f"invalid={{entity.invalid_count}} failed={{entity.failed_count}}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _generated_test_template(source: str, base_url: str) -> str:
    prefix = source.upper()
    return f"""from felts.sources.{source}.constants import (
    {prefix}_BASE_URL,
    ENDPOINTS,
)
from felts.sources.{source}.deployments import build_source_deployment_specs


def test_generated_source_defaults() -> None:
    assert {prefix}_BASE_URL == {base_url!r}
    assert [spec.entity for spec in build_source_deployment_specs()] == list(ENDPOINTS)


# scaffold: entity-tests:start
# scaffold: entity-tests:end
"""


def _entity_test(spec: EntitySpec) -> str:
    runtime_values = {name: [f"{name}-value"] for name in spec.runtime_params}
    expected_payload: dict[str, object] = {
        name: values[0] for name, values in runtime_values.items()
    }
    if spec.response_shape == "list":
        response = '[{"value": 1}]'
    elif spec.response_shape == "data_object":
        response = '{"data": {"value": 1}}'
    elif spec.response_shape == "keyed_object":
        response = (
            "{"
            + repr(spec.records_path or "records")
            + ": {"
            + repr("record-key")
            + ': {"value": 1}}}'
        )
        expected_payload[spec.key_field or "key"] = "record-key"
    else:
        response = '{"value": 1}'
    expected_payload["value"] = 1
    return f"""def test_{spec.entity}_endpoint_shape() -> None:
    from unittest.mock import Mock

    from felts.sources.{spec.source}.extractor import {_class_name(spec.source)}Extractor

    client = Mock()
    client.get_json.return_value = {response}
    records = {_class_name(spec.source)}Extractor(client=client).extract_entity(
        {spec.entity!r},
        runtime_params={runtime_values!r},
    )

    assert len(records) == 1
    assert records[0].payload == {expected_payload!r}
"""


def _staging_sql(spec: EntitySpec) -> str:
    return f"""-- TODO(scaffold): select analytical fields and document declared grain.
select
    id as raw_record_id,
    source_record_id,
    extracted_at,
    observed_at,
    loaded_at,
    batch_id,
    payload as raw_payload
from {{{{ source('{spec.source}', 'raw_{spec.entity}') }}}}
where is_valid
"""


def _apply_transaction(
    root: Path,
    writes: dict[Path, str],
    *,
    generated_python: Sequence[Path],
    test_path: Path,
    run_checks: bool,
) -> None:
    for path in writes:
        if not path.is_relative_to(root):
            raise ScaffoldError(f"refusing to write outside repository: {path}")
    for path, content in writes.items():
        if path.suffix == ".py":
            try:
                ast.parse(content, filename=str(path))
            except SyntaxError as exc:
                raise ScaffoldError(f"generated invalid Python for {path}: {exc}") from exc

    originals = {path: path.read_bytes() if path.exists() else None for path in writes}
    missing_parents = {
        parent
        for path in writes
        for parent in path.parents
        if parent != root and parent.is_relative_to(root) and not parent.exists()
    }
    new_roots = {
        parent
        for parent in missing_parents
        if not any(ancestor in missing_parents for ancestor in parent.parents)
    }
    try:
        for path, content in writes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        if run_checks:
            _run_fast_checks(root, generated_python, test_path)
    except Exception:
        for path, original in originals.items():
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
        for directory in new_roots:
            shutil.rmtree(directory, ignore_errors=True)
        raise


def _run_fast_checks(
    root: Path,
    generated_python: Sequence[Path],
    test_path: Path,
) -> None:
    relative_python = [str(path.relative_to(root)) for path in generated_python]
    commands = [
        ["uv", "run", "ruff", "format", *relative_python],
        ["uv", "run", "ruff", "check", *relative_python],
        ["uv", "run", "pytest", str(test_path.relative_to(root))],
        [
            "uv",
            "run",
            "dbt",
            "parse",
            "--project-dir",
            "transforms",
            "--profiles-dir",
            "transforms",
        ],
    ]
    for command in commands:
        try:
            subprocess.run(command, cwd=root, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ScaffoldError(f"validation failed: {' '.join(command)}") from exc


def _append_managed_line(content: str, block: str, addition: str) -> str:
    start = f"# scaffold: {block}:start"
    end = f"# scaffold: {block}:end"
    if content.count(start) != 1 or content.count(end) != 1:
        raise ScaffoldError(f"managed block {block!r} is missing or ambiguous")
    if content.index(start) > content.index(end):
        raise ScaffoldError(f"managed block {block!r} has invalid marker order")
    before, remainder = content.split(start, 1)
    body, after = remainder.split(end, 1)
    if addition.strip() in body:
        raise ScaffoldError(f"managed block collision for {addition.strip()!r}")
    existing = body.strip("\n")
    replacement = "\n"
    if existing.strip():
        replacement += existing + "\n"
    replacement += addition.rstrip() + "\n"
    return before + start + replacement + end + after


def _validate_entity_spec(spec: EntitySpec) -> None:
    _validate_identifier("source", spec.source)
    _validate_identifier("entity", spec.entity)
    if not spec.path.startswith("/"):
        raise ScaffoldError("endpoint path must start with '/'")
    if spec.response_shape not in RESPONSE_SHAPES:
        raise ScaffoldError(f"unsupported response shape: {spec.response_shape}")
    if spec.response_shape == "keyed_object":
        if not spec.records_path or not spec.key_field:
            raise ScaffoldError("keyed_object requires --records-path and --key-field")
    elif spec.records_path or spec.key_field:
        raise ScaffoldError("--records-path and --key-field are only valid for keyed_object")
    param_names = [key for key, _ in spec.params]
    names = [*spec.id_fields, *spec.runtime_params, *param_names]
    for name in names:
        _validate_identifier("parameter", name)
    for label, values in (
        ("identity fields", spec.id_fields),
        ("runtime parameters", spec.runtime_params),
        ("static parameters", param_names),
    ):
        if len(values) != len(set(values)):
            raise ScaffoldError(f"{label} must be unique")
    if set(spec.runtime_params) & set(param_names):
        raise ScaffoldError("static and runtime parameter names must not overlap")


def _validate_identifier(label: str, value: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ScaffoldError(
            f"{label} must be normalized snake_case starting with a letter: {value!r}"
        )


def _validate_base_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ScaffoldError(f"base URL must be an absolute HTTP(S) URL: {value!r}")


def _parse_param(value: str) -> tuple[str, str]:
    key, separator, param_value = value.partition("=")
    if not separator or not key or not param_value:
        raise ScaffoldError(f"--param must use key=value: {value!r}")
    return key, param_value


def _read_required(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError as exc:
        raise ScaffoldError(f"required file does not exist: {path}") from exc


def _python_paths(writes: dict[Path, str]) -> tuple[Path, ...]:
    return tuple(path for path in writes if path.suffix == ".py")


def _class_name(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_"))


def _title(value: str) -> str:
    return value.replace("_", " ").title()


def _print_source_next_steps(source: str) -> None:
    print(f"scaffolded source={source}")
    print(f"next: add an entity with scripts/scaffold.py entity {source} <entity> ...")
    print("next: add typed credential settings and .env.*.example keys if required")
    print("next: run the provider live test, then review scheduling and rate limits")
    print("next: re-run make prefect-register after deployments are ready")


def _print_entity_next_steps(spec: EntitySpec) -> None:
    print(f"scaffolded source={spec.source} entity={spec.entity}")
    print("next: replace the permissive payload schema with required provider fields")
    print("next: verify identity fields and missing-identity validation")
    print("next: select dbt fields, types, tests, and document declared grain")
    print("next: add custom pagination logic if this endpoint paginates")
    print("next: perform a credential-safe live test")
    print("next: review rate limits before adding a schedule")
    print("next: run the full unit, integration, mypy, and Prefect checks")
    print("next: re-run make prefect-register after deployment parameters are complete")


if __name__ == "__main__":
    raise SystemExit(main())

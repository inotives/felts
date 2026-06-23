"""CSV import Prefect deployment definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from prefect.deployments.runner import RunnerDeployment

from felts.config import Settings
from felts.sources.csv_import.contracts import load_csv_contracts
from felts.sources.csv_import.flow import csv_import_source_flow


@dataclass(frozen=True)
class CsvDeploymentSpec:
    name: str
    contract: str
    is_backfill: bool = False

    @property
    def parameters(self) -> dict[str, str]:
        return {"contract": self.contract}


def build_source_deployment_specs() -> tuple[CsvDeploymentSpec, ...]:
    specs: list[CsvDeploymentSpec] = []
    for contract_id in load_csv_contracts():
        name = contract_id.replace("_", "-")
        specs.append(CsvDeploymentSpec(name=f"csv-import-{name}-source", contract=contract_id))
        specs.append(
            CsvDeploymentSpec(
                name=f"csv-import-{name}-backfill",
                contract=contract_id,
                is_backfill=True,
            )
        )
    return tuple(specs)


def deploy_source_flows(settings: Settings) -> list[str]:
    deployment_names: list[str] = []
    for spec in build_source_deployment_specs():
        deployment = cast(
            RunnerDeployment,
            csv_import_source_flow.to_deployment(
                name=spec.name,
                work_pool_name=settings.prefect_work_pool,
                work_queue_name=settings.prefect_work_queue,
                parameters=spec.parameters,
                job_variables={"working_dir": str(settings.resolve_project_path(Path(".")))},
                tags=["csv_import", "source", spec.contract]
                + (["backfill"] if spec.is_backfill else []),
                description=(
                    f"CSV import {spec.contract} "
                    f"{'backfill' if spec.is_backfill else 'source'} deployment."
                ),
            ),
        )
        deployment.apply(work_pool_name=settings.prefect_work_pool)
        deployment_names.append(spec.name)
    return deployment_names

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

    @property
    def parameters(self) -> dict[str, str]:
        return {"contract": self.contract}


def build_source_deployment_specs() -> tuple[CsvDeploymentSpec, ...]:
    return tuple(
        CsvDeploymentSpec(
            name=f"csv-import-{contract_id.replace('_', '-')}-source",
            contract=contract_id,
        )
        for contract_id in load_csv_contracts()
    )


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
                tags=["csv_import", "source", spec.contract],
                description=f"CSV import {spec.contract} source deployment.",
            ),
        )
        deployment.apply(work_pool_name=settings.prefect_work_pool)
        deployment_names.append(spec.name)
    return deployment_names

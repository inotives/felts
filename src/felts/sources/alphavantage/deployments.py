"""Generated manual Alphavantage deployment definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from prefect.deployments.runner import RunnerDeployment

from felts.config import Settings
from felts.sources.alphavantage.constants import ENDPOINTS
from felts.sources.alphavantage.flow import alphavantage_source_flow


@dataclass(frozen=True)
class SourceDeploymentSpec:
    name: str
    entity: str

    @property
    def parameters(self) -> dict[str, object]:
        endpoint = ENDPOINTS[self.entity]
        runtime_params: dict[str, list[str]] = {name: [] for name in endpoint.runtime_params}
        if self.entity == "time_series_daily":
            runtime_params["symbol"] = ["SPCX", "AAPL", "TSM", "NVDA"]
        return {
            "entities": [self.entity],
            "runtime_params": runtime_params,
        }


def build_source_deployment_specs() -> tuple[SourceDeploymentSpec, ...]:
    return tuple(
        SourceDeploymentSpec(
            name=f"alphavantage-{entity.replace('_', '-')}-source",
            entity=entity,
        )
        for entity in ENDPOINTS
    )


def deploy_source_flows(settings: Settings) -> list[str]:
    names = []
    for spec in build_source_deployment_specs():
        deployment = cast(
            RunnerDeployment,
            alphavantage_source_flow.to_deployment(
                name=spec.name,
                work_pool_name=settings.prefect_work_pool,
                work_queue_name=settings.prefect_work_queue,
                schedules=None,
                parameters=spec.parameters,
                job_variables={"working_dir": str(settings.resolve_project_path(Path(".")))},
                tags=["alphavantage", "source", spec.entity],
                description=f"Alpha Vantage {spec.entity} manual source deployment.",
            ),
        )
        deployment.apply(work_pool_name=settings.prefect_work_pool)
        names.append(spec.name)
    return names

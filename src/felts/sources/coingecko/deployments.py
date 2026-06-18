"""CoinGecko Prefect deployment definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from prefect.deployments.runner import RunnerDeployment
from prefect.schedules import Schedule

from felts.config import Settings
from felts.sources.coingecko.constants import (
    COINGECKO_SOURCE_DEPLOYMENT_PREFIX,
    SCHEDULED_ENTITIES,
    SUPPORTED_ENTITIES,
    CoinGeckoEntity,
)
from felts.sources.coingecko.flow import coingecko_entity_source_flow


@dataclass(frozen=True)
class SourceDeploymentSpec:
    name: str
    entity: CoinGeckoEntity
    cron: str | None

    @property
    def parameters(self) -> dict[str, str]:
        return {"entity": self.entity}

    @property
    def schedules(self) -> list[Schedule] | None:
        if self.cron is None:
            return None
        return [Schedule(cron=self.cron, timezone="UTC", active=True)]


COINGECKO_ENTITY_SCHEDULES: dict[CoinGeckoEntity, str] = {
    "coins_list": "0 0 * * *",
    "asset_platforms_list": "15 0 * * *",
    "global": "0 * * * *",
    "global_defi": "15 * * * *",
}


def build_source_deployment_specs() -> tuple[SourceDeploymentSpec, ...]:
    specs: list[SourceDeploymentSpec] = []
    for entity in SUPPORTED_ENTITIES:
        cron = COINGECKO_ENTITY_SCHEDULES.get(entity) if entity in SCHEDULED_ENTITIES else None
        specs.append(
            SourceDeploymentSpec(
                name=f"{COINGECKO_SOURCE_DEPLOYMENT_PREFIX}-{entity.replace('_', '-')}-source",
                entity=entity,
                cron=cron,
            )
        )
    return tuple(specs)


def deploy_source_flows(settings: Settings) -> list[str]:
    deployment_names: list[str] = []
    for spec in build_source_deployment_specs():
        deployment = cast(
            RunnerDeployment,
            coingecko_entity_source_flow.to_deployment(
                name=spec.name,
                work_pool_name=settings.prefect_work_pool,
                work_queue_name=settings.prefect_work_queue,
                schedules=spec.schedules,
                parameters=spec.parameters,
                job_variables={"working_dir": str(settings.resolve_project_path(Path(".")))},
                tags=["coingecko", "source", spec.entity],
                description=f"CoinGecko {spec.entity} source entity deployment.",
            ),
        )
        deployment.apply(work_pool_name=settings.prefect_work_pool)
        deployment_names.append(spec.name)
    return deployment_names

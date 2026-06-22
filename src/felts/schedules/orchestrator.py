"""Prefect deployment registration entrypoint."""

import asyncio
from pathlib import Path
from typing import cast

from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolCreate
from prefect.deployments.runner import RunnerDeployment

from felts.config import Settings, get_settings
from felts.flows.transform import transform_flow
from felts.sources.coingecko.automations import build_transform_triggers as coingecko_triggers
from felts.sources.coingecko.deployments import deploy_source_flows as deploy_coingecko_flows
from felts.sources.csv_import.automations import build_transform_triggers as csv_triggers
from felts.sources.csv_import.deployments import deploy_source_flows as deploy_csv_flows


async def ensure_work_pool(settings: Settings) -> None:
    async with get_client() as client:
        try:
            await client.read_work_pool(settings.prefect_work_pool)
        except Exception:
            await client.create_work_pool(
                WorkPoolCreate(
                    name=settings.prefect_work_pool,
                    type=settings.prefect_work_pool_type,
                ),
                overwrite=True,
            )

        try:
            await client.read_work_queue_by_name(
                settings.prefect_work_queue,
                work_pool_name=settings.prefect_work_pool,
            )
        except Exception:
            await client.create_work_queue(
                name=settings.prefect_work_queue,
                work_pool_name=settings.prefect_work_pool,
            )


def deploy_transform_flow(settings: Settings) -> str:
    deployment_name = "dbt-transform"
    triggers = [*coingecko_triggers(), *csv_triggers()]
    deployment = cast(
        RunnerDeployment,
        transform_flow.to_deployment(
            name=deployment_name,
            work_pool_name=settings.prefect_work_pool,
            work_queue_name=settings.prefect_work_queue,
            triggers=triggers,
            job_variables={"working_dir": str(settings.resolve_project_path(Path(".")))},
            tags=["dbt", "transform"],
            description="Generic parameterized dbt transform deployment.",
        ),
    )
    deployment.apply(work_pool_name=settings.prefect_work_pool)
    return deployment_name


def register_all(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    asyncio.run(ensure_work_pool(settings))
    registered = [deploy_transform_flow(settings)]
    registered.extend(deploy_coingecko_flows(settings))
    registered.extend(deploy_csv_flows(settings))
    return registered


def main() -> int:
    for deployment_name in register_all():
        print(f"registered={deployment_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CoinGecko event-to-transform trigger definitions."""

from prefect.events import DeploymentEventTrigger, DeploymentTriggerTypes, TriggerTypes

from felts.sources.coingecko.constants import DBT_SELECTORS, SUPPORTED_ENTITIES
from felts.sources.coingecko.events import raw_completion_event_name, raw_completion_resource_id


def build_transform_triggers() -> list[DeploymentTriggerTypes | TriggerTypes]:
    triggers: list[DeploymentTriggerTypes | TriggerTypes] = []
    for entity in SUPPORTED_ENTITIES:
        triggers.append(
            DeploymentEventTrigger(
                name=f"coingecko-{entity.replace('_', '-')}-raw-completed-to-dbt-transform",
                expect={raw_completion_event_name(entity)},
                match={"prefect.resource.id": raw_completion_resource_id(entity)},
                parameters={"selector": DBT_SELECTORS[entity], "run_tests": True},
            )
        )
    return triggers

"""Generated Alphavantage event-to-transform triggers."""

from prefect.events import DeploymentEventTrigger, DeploymentTriggerTypes, TriggerTypes

from felts.sources.alphavantage.constants import DBT_SELECTORS, SUPPORTED_ENTITIES
from felts.sources.alphavantage.events import raw_completion_event_name, raw_completion_resource_id


def build_transform_triggers() -> list[DeploymentTriggerTypes | TriggerTypes]:
    return [
        DeploymentEventTrigger(
            name=f"alphavantage-{entity.replace('_', '-')}-raw-completed-to-dbt-transform",
            expect={raw_completion_event_name(entity)},
            match={"prefect.resource.id": raw_completion_resource_id(entity)},
            parameters={"selector": DBT_SELECTORS[entity], "run_tests": True},
        )
        for entity in SUPPORTED_ENTITIES
    ]

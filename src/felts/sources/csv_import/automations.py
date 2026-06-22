"""CSV event-to-transform trigger definitions."""

from prefect.events import DeploymentEventTrigger, DeploymentTriggerTypes, TriggerTypes

from felts.sources.csv_import.contracts import load_csv_contracts
from felts.sources.csv_import.events import raw_completion_event_name, raw_completion_resource_id


def build_transform_triggers() -> list[DeploymentTriggerTypes | TriggerTypes]:
    triggers: list[DeploymentTriggerTypes | TriggerTypes] = []
    for contract in load_csv_contracts().values():
        triggers.append(
            DeploymentEventTrigger(
                name=(
                    f"csv-import-{contract.entity.replace('_', '-')}-raw-completed-to-dbt-transform"
                ),
                expect={raw_completion_event_name(contract.entity)},
                match={"prefect.resource.id": raw_completion_resource_id(contract.entity)},
                parameters={"selector": contract.dbt_selector, "run_tests": True},
            )
        )
    return triggers

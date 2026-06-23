"""CSV import Prefect source flow."""

from prefect import flow

from felts.core.sources import SourceRunSummary
from felts.sources.csv_import.events import emit_raw_completion_events
from felts.sources.csv_import.runner import run_csv_import


@flow(name="csv-import-source", retries=2, retry_delay_seconds=60)
def csv_import_source_flow(
    contract: str,
    input_uri: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> SourceRunSummary:
    summary = run_csv_import(
        contract_id=contract,
        input_uri=input_uri,
        start_date=start_date,
        end_date=end_date,
    )
    emit_raw_completion_events(summary)
    return summary

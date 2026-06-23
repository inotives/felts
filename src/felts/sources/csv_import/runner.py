"""Plain Python CSV import runner."""

from datetime import UTC, datetime

from felts.config import Settings, get_settings
from felts.core.exceptions import ConfigurationError
from felts.core.extractors.csv import CsvFileExtractor, parse_date_bound
from felts.core.loaders import RawWriter, create_loader
from felts.core.schemas import SchemaRegistry
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.csv_import.contracts import (
    CSV_IMPORT_SOURCE,
    get_csv_contract,
    load_csv_contracts,
)
from felts.sources.csv_import.schemas import CsvRawPayload

SCHEMA_VERSION = "1"


def build_csv_schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    for contract in load_csv_contracts().values():
        registry.register(
            source=contract.source,
            entity=contract.entity,
            model=CsvRawPayload,
            schema_name=f"{contract.source}_{contract.entity}",
            schema_version=SCHEMA_VERSION,
        )
    return registry


def run_csv_import(
    *,
    contract_id: str,
    input_uri: str,
    start_date: str | None = None,
    end_date: str | None = None,
    settings: Settings | None = None,
    writer: RawWriter | None = None,
) -> SourceRunSummary:
    started_at = datetime.now(UTC)
    settings = settings or get_settings()
    contract = get_csv_contract(contract_id)
    if writer is None:
        writer = RawWriter(
            schema_registry=build_csv_schema_registry(),
            loader=create_loader(settings),
            loader_batch_size=settings.loader_batch_size,
        )
    start = parse_date_bound(start_date, field_name="start_date")
    end = parse_date_bound(end_date, field_name="end_date")
    if start is not None and end is not None and start > end:
        msg = "start_date must be before or equal to end_date"
        raise ConfigurationError(msg)
    result = writer.write(
        CsvFileExtractor(
            contract=contract,
            input_uri=input_uri,
            start_date=start,
            end_date=end,
        ).extract()
    )
    return SourceRunSummary(
        source=CSV_IMPORT_SOURCE,
        started_at=started_at,
        ended_at=datetime.now(UTC),
        entities=(EntityRunSummary.from_write_result(entity=contract.entity, result=result),),
    )

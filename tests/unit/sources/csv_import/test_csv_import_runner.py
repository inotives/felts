from collections.abc import Sequence

from felts.core.loaders import LoadResult, RawWriter
from felts.core.schemas import RawRecord
from felts.sources.csv_import.runner import build_csv_schema_registry, run_csv_import


class MemoryLoader:
    def __init__(self) -> None:
        self.records: list[RawRecord] = []

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        self.records.extend(records)
        return LoadResult(inserted_count=len(records))


def test_run_csv_import_returns_summary() -> None:
    loader = MemoryLoader()
    writer = RawWriter(schema_registry=build_csv_schema_registry(), loader=loader)

    summary = run_csv_import(
        contract_id="fred_series",
        input_uri="tests/fixtures/csv_import/fred_series.csv",
        writer=writer,
    )

    assert summary.source == "csv_import"
    assert summary.entities[0].entity == "fred_series"
    assert summary.entities[0].extracted_count == 1
    assert summary.entities[0].inserted_count == 1
    assert loader.records[0].is_valid is True


def test_run_csv_import_accepts_backfill_date_bounds() -> None:
    loader = MemoryLoader()
    writer = RawWriter(schema_registry=build_csv_schema_registry(), loader=loader)

    summary = run_csv_import(
        contract_id="fred_series",
        input_uri="tests/fixtures/csv_import/fred_series.csv",
        start_date="2026-06-01",
        end_date="2026-06-30",
        writer=writer,
    )

    assert summary.entities[0].extracted_count == 0
    assert loader.records == []

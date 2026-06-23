from felts.sources.csv_import.deployments import build_source_deployment_specs


def test_build_source_deployment_specs_registers_csv_contracts_without_schedules() -> None:
    specs = build_source_deployment_specs()

    assert [spec.contract for spec in specs] == ["ohlcv", "ohlcv", "fred_series", "fred_series"]
    assert specs[0].name == "csv-import-ohlcv-source"
    assert specs[0].parameters == {"contract": "ohlcv"}
    assert specs[1].name == "csv-import-ohlcv-backfill"
    assert specs[1].is_backfill is True

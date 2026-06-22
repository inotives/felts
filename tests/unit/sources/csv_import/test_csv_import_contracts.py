from felts.sources.csv_import.contracts import load_csv_contracts


def test_load_csv_contracts() -> None:
    contracts = load_csv_contracts()

    assert set(contracts) == {"ohlcv", "fred_series"}
    assert contracts["ohlcv"].delimiter == ";"
    assert contracts["fred_series"].allow_extra_headers is True

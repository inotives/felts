from datetime import UTC, datetime

from pytest import CaptureFixture, MonkeyPatch

from felts import cli


def test_top_level_cli_dispatches_csv_import(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    from felts.core.sources import EntityRunSummary, SourceRunSummary

    def fake_run_csv_import(
        *,
        contract_id: str,
        input_uri: str,
        start_date: str | None,
        end_date: str | None,
    ) -> SourceRunSummary:
        assert contract_id == "fred_series"
        assert input_uri == "data/fred/us_cpi-202605.csv"
        assert start_date is None
        assert end_date is None
        return SourceRunSummary(
            source="csv_import",
            started_at=datetime.now(UTC),
            entities=(
                EntityRunSummary(
                    entity="fred_series",
                    batch_id="batch-1",
                    extracted_count=1,
                    inserted_count=1,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=0,
                ),
            ),
        )

    monkeypatch.setattr("felts.sources.csv_import.cli.run_csv_import", fake_run_csv_import)

    exit_code = cli.main(
        ["csv", "import", "--contract", "fred_series", "--input-uri", "data/fred/us_cpi-202605.csv"]
    )

    assert exit_code == 0
    assert "source=csv_import" in capsys.readouterr().out


def test_top_level_cli_dispatches_ccxt(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    from felts.core.sources import EntityRunSummary, SourceRunSummary

    def fake_run_ccxt_source(*, entities: list[str] | None) -> SourceRunSummary:
        assert entities == ["ticker", "order_book"]
        return SourceRunSummary(
            source="ccxt",
            started_at=datetime.now(UTC),
            entities=(
                EntityRunSummary(
                    entity="ticker",
                    batch_id="batch-1",
                    extracted_count=1,
                    inserted_count=1,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=0,
                ),
            ),
        )

    monkeypatch.setattr("felts.sources.ccxt.cli.run_ccxt_source", fake_run_ccxt_source)

    exit_code = cli.main(["ccxt", "run", "--entities", "ticker", "order_book"])

    assert exit_code == 0
    assert "source=ccxt" in capsys.readouterr().out

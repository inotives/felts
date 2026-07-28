from datetime import UTC, datetime

from pytest import CaptureFixture, MonkeyPatch

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.ccxt import cli


def test_cli_prints_summary(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
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
                EntityRunSummary(
                    entity="order_book",
                    batch_id="batch-2",
                    extracted_count=1,
                    inserted_count=1,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=0,
                ),
            ),
        )

    monkeypatch.setattr(cli, "run_ccxt_source", fake_run_ccxt_source)

    exit_code = cli.main(["ccxt", "run", "--entities", "ticker", "order_book"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "source=ccxt" in output
    assert "entity=ticker extracted=1 inserted=1" in output
    assert "entity=order_book extracted=1 inserted=1" in output


def test_cli_returns_nonzero_when_any_entity_fails(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
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
                EntityRunSummary(
                    entity="order_book",
                    batch_id="batch-2",
                    extracted_count=0,
                    inserted_count=0,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=1,
                ),
            ),
        )

    monkeypatch.setattr(cli, "run_ccxt_source", fake_run_ccxt_source)

    exit_code = cli.main(["ccxt", "run", "--entities", "ticker", "order_book"])

    assert exit_code == 1
    assert "source=ccxt" in capsys.readouterr().out

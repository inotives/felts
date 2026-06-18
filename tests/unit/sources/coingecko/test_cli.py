from datetime import UTC, datetime

from pytest import CaptureFixture, MonkeyPatch

from felts.sources.coingecko import cli


def test_cli_prints_summary(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    from felts.core.sources import EntityRunSummary, SourceRunSummary

    def fake_run_coingecko_source(*, entities: list[str] | None) -> SourceRunSummary:
        assert entities == ["coins_list", "global"]
        return SourceRunSummary(
            source="coingecko",
            started_at=datetime.now(UTC),
            entities=(
                EntityRunSummary(
                    entity="coins_list",
                    batch_id="batch-1",
                    extracted_count=1,
                    inserted_count=1,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=0,
                ),
            ),
        )

    monkeypatch.setattr(cli, "run_coingecko_source", fake_run_coingecko_source)

    exit_code = cli.main(["coingecko", "run", "--entities", "coins_list", "global"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "source=coingecko" in output
    assert "entity=coins_list extracted=1 inserted=1" in output

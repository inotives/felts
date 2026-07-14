from datetime import UTC, datetime

import pytest
from pytest import CaptureFixture, MonkeyPatch

from felts import cli as top_level_cli
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.agent_pipe import cli


def test_cli_prints_summary(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    def fake_run_agent_pipe_import(
        *, sqlite_path: str, updated_since: str | None
    ) -> SourceRunSummary:
        assert sqlite_path == "local.sqlite"
        assert updated_since == "2026-07-14T02:00:00Z"
        return SourceRunSummary(
            source="agent_pipe",
            started_at=datetime.now(UTC),
            entities=(
                EntityRunSummary(
                    entity="note",
                    batch_id="batch-1",
                    extracted_count=2,
                    inserted_count=2,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=0,
                ),
            ),
        )

    monkeypatch.setattr(cli, "run_agent_pipe_import", fake_run_agent_pipe_import)

    parser = top_level_cli._build_parser()
    args = parser.parse_args(
        [
            "agent-pipe",
            "import",
            "--sqlite-path",
            "local.sqlite",
            "--updated-since",
            "2026-07-14T02:00:00Z",
        ]
    )
    exit_code = args.handler(args)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "source=agent_pipe" in output
    assert "entity=note extracted=2 inserted=2" in output


def test_cli_requires_sqlite_path() -> None:
    parser = top_level_cli._build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["agent-pipe", "import"])

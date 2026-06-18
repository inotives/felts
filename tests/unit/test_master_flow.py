from datetime import UTC, datetime

from pytest import MonkeyPatch

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.flows import master


def test_master_flow_runs_transform_only_when_entity_inserts(monkeypatch: MonkeyPatch) -> None:
    transformed_selectors: list[str] = []

    def fake_coingecko_entity_source_flow(entity: str) -> SourceRunSummary:
        return SourceRunSummary(
            source="coingecko",
            started_at=datetime.now(UTC),
            entities=(
                EntityRunSummary(
                    entity=entity,
                    batch_id="batch-1",
                    extracted_count=1,
                    inserted_count=1 if entity == "coins_list" else 0,
                    skipped_duplicate_count=0,
                    invalid_count=0,
                    failed_count=0,
                ),
            ),
        )

    def fake_transform_flow(selector: str, run_tests: bool = True) -> None:
        transformed_selectors.append(selector)

    monkeypatch.setattr(master, "coingecko_entity_source_flow", fake_coingecko_entity_source_flow)
    monkeypatch.setattr(master, "transform_flow", fake_transform_flow)

    master.master_flow.fn(source="coingecko", entities=["coins_list", "global"])

    assert transformed_selectors == ["stg_coingecko__coins_list+"]

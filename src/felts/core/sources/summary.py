"""Reusable source-run summary contracts."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from felts.core.loaders import WriteResult


@dataclass(frozen=True)
class EntityRunSummary:
    entity: str
    batch_id: str
    extracted_count: int
    inserted_count: int
    skipped_duplicate_count: int
    invalid_count: int
    failed_count: int

    @classmethod
    def from_write_result(cls, *, entity: str, result: WriteResult) -> "EntityRunSummary":
        return cls(
            entity=entity,
            batch_id=result.batch_id,
            extracted_count=result.received_count,
            inserted_count=result.loaded_count,
            skipped_duplicate_count=result.skipped_count,
            invalid_count=result.invalid_count,
            failed_count=result.failed_count,
        )


@dataclass(frozen=True)
class SourceRunSummary:
    source: str
    started_at: datetime
    ended_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    entities: tuple[EntityRunSummary, ...] = ()

    @property
    def extracted_count(self) -> int:
        return sum(entity.extracted_count for entity in self.entities)

    @property
    def inserted_count(self) -> int:
        return sum(entity.inserted_count for entity in self.entities)

    @property
    def skipped_duplicate_count(self) -> int:
        return sum(entity.skipped_duplicate_count for entity in self.entities)

    @property
    def invalid_count(self) -> int:
        return sum(entity.invalid_count for entity in self.entities)

    @property
    def failed_count(self) -> int:
        return sum(entity.failed_count for entity in self.entities)

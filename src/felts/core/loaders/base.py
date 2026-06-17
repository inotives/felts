"""Loader contracts and result types."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from felts.core.schemas import RawRecord

ResultStage = Literal["validation", "load"]


@dataclass(frozen=True)
class ResultError:
    source: str
    entity: str
    stage: ResultStage
    message: str
    record_id: str | None = None
    details: dict[str, Any] | list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class LoadResult:
    inserted_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    errors: list[ResultError] = field(default_factory=list)


@dataclass(frozen=True)
class WriteResult:
    batch_id: str
    received_count: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    loaded_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    errors: list[ResultError] = field(default_factory=list)


class BaseLoader(Protocol):
    """Persistence boundary for raw records."""

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        """Persist raw records and return database-facing outcomes."""

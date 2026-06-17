"""Base extractor contract."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from felts.core.schemas import ExtractedRecord


class BaseExtractor(ABC):
    """Extractor implementations emit extracted records."""

    @abstractmethod
    def extract(self) -> Iterable[ExtractedRecord]:
        """Yield extracted records."""

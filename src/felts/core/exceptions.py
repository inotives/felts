"""Shared Felts exception types."""


class FeltsError(Exception):
    """Base exception for Felts failures."""


class ConfigurationError(FeltsError):
    """Raised when project configuration is invalid or incomplete."""


class ValidationSetupError(FeltsError):
    """Raised when schema validation is configured incorrectly."""


class WriterInputError(FeltsError):
    """Raised when writer input violates the writer contract."""


class LoaderError(FeltsError):
    """Raised when a loader cannot complete a persistence operation."""


class ExtractionError(FeltsError):
    """Raised when a source extractor cannot complete a request or parse a response."""

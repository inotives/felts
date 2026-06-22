"""Standard-library CSV extraction helpers."""

import csv
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from felts.config.settings import REPO_ROOT
from felts.core.exceptions import ConfigurationError, ExtractionError
from felts.core.schemas import ExtractedRecord


@dataclass(frozen=True)
class CsvIdentity:
    strategy: str
    pattern: str | None = None
    value_header_index: int | None = None


@dataclass(frozen=True)
class CsvContract:
    contract_id: str
    source: str
    entity: str
    delimiter: str
    encoding: str
    required_headers: tuple[str, ...]
    allow_extra_headers: bool
    identity: CsvIdentity
    source_record_id_fields: tuple[str, ...]
    observed_column: str
    dbt_selector: str


class CsvFileExtractor:
    def __init__(self, *, contract: CsvContract, input_uri: str) -> None:
        self.contract = contract
        self.input_uri = input_uri

    def extract(self) -> Iterable[ExtractedRecord]:
        path = resolve_local_input_uri(self.input_uri)
        identity = self._extract_identity(path)
        with path.open("r", encoding=self.contract.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self.contract.delimiter)
            headers = tuple(reader.fieldnames or ())
            validate_headers(contract=self.contract, headers=headers)
            for row_number, row in enumerate(reader, start=2):
                yield self._record(row=row, row_number=row_number, identity=identity)

    def _extract_identity(self, path: Path) -> dict[str, str]:
        match self.contract.identity.strategy:
            case "filename_pattern":
                if self.contract.identity.pattern is None:
                    msg = f"{self.contract.contract_id} identity pattern is required"
                    raise ConfigurationError(msg)
                match_result = re.match(self.contract.identity.pattern, path.name)
                if match_result is None:
                    msg = f"{path.name} does not match {self.contract.contract_id} filename pattern"
                    raise ExtractionError(msg)
                return {key: str(value) for key, value in match_result.groupdict().items()}
            case "value_column_header":
                return {}
            case _:
                msg = f"unsupported CSV identity strategy: {self.contract.identity.strategy}"
                raise ConfigurationError(msg)

    def _record(
        self,
        *,
        row: dict[str, str | None],
        row_number: int,
        identity: dict[str, str],
    ) -> ExtractedRecord:
        values = {key: value for key, value in row.items() if key is not None}
        row_identity = dict(identity)
        if self.contract.identity.strategy == "value_column_header":
            value_headers = [
                key
                for key in values
                if key not in self.contract.required_headers and key is not None
            ]
            index = self.contract.identity.value_header_index or 0
            if index >= len(value_headers):
                msg = f"{self.contract.contract_id} value column header is missing"
                raise ExtractionError(msg)
            row_identity["series_id"] = value_headers[index]

        observed_raw = values.get(self.contract.observed_column)
        observed_at = parse_csv_datetime(observed_raw)
        validation_errors: list[dict[str, str]] = []
        if observed_at is None:
            validation_errors.append(
                {
                    "path": self.contract.observed_column,
                    "message": "observed value is required",
                    "type": "csv_observed_required",
                }
            )
        for field in missing_identity_fields(
            fields=self.contract.source_record_id_fields,
            row=values,
            identity=row_identity,
        ):
            validation_errors.append(
                {
                    "path": field,
                    "message": "source record identity value is required",
                    "type": "csv_identity_required",
                }
            )

        felts_metadata: dict[str, Any] = {
            "contract": self.contract.contract_id,
            "input_uri": self.input_uri,
            "row_number": row_number,
            "identity": row_identity,
        }
        if validation_errors:
            felts_metadata["validation_errors"] = validation_errors

        payload: dict[str, Any] = dict(values)
        payload["_felts"] = felts_metadata
        return ExtractedRecord(
            source=self.contract.source,
            entity=self.contract.entity,
            payload=payload,
            observed_at=observed_at,
            source_record_id=source_record_id(
                fields=self.contract.source_record_id_fields,
                row=values,
                identity=row_identity,
                row_number=row_number,
            ),
        )


def resolve_local_input_uri(input_uri: str) -> Path:
    parsed = urlparse(input_uri)
    if parsed.scheme in ("http", "https", "s3", "gs"):
        msg = f"unsupported CSV input URI scheme: {parsed.scheme}"
        raise ConfigurationError(msg)
    if parsed.scheme == "file":
        path = Path(unquote(parsed.path))
    elif parsed.scheme == "":
        path = Path(input_uri)
    else:
        msg = f"unsupported CSV input URI scheme: {parsed.scheme}"
        raise ConfigurationError(msg)
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.is_file():
        msg = f"CSV input file not found: {path}"
        raise ExtractionError(msg)
    return path


def validate_headers(*, contract: CsvContract, headers: tuple[str, ...]) -> None:
    missing = [header for header in contract.required_headers if header not in headers]
    if missing:
        msg = f"{contract.contract_id} CSV is missing required headers: {', '.join(missing)}"
        raise ExtractionError(msg)
    if not contract.allow_extra_headers:
        extra = [header for header in headers if header not in contract.required_headers]
        if extra:
            msg = f"{contract.contract_id} CSV has unsupported headers: {', '.join(extra)}"
            raise ExtractionError(msg)


def parse_csv_datetime(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed_date = datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
        return datetime.combine(parsed_date, time.min, tzinfo=UTC)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def source_record_id(
    *,
    fields: tuple[str, ...],
    row: dict[str, str | None],
    identity: dict[str, str],
    row_number: int,
) -> str:
    parts: list[str] = []
    for field in fields:
        if field == "row_number":
            parts.append(str(row_number))
        elif field in identity:
            parts.append(identity[field])
        else:
            value = row.get(field)
            parts.append("" if value is None else value)
    return "|".join(parts)


def missing_identity_fields(
    *,
    fields: tuple[str, ...],
    row: dict[str, str | None],
    identity: dict[str, str],
) -> list[str]:
    return [
        field
        for field in fields
        if field != "row_number" and field not in identity and not row.get(field)
    ]

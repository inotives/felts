"""CSV import contract registry."""

from pathlib import Path
from typing import Any, cast

import yaml

from felts.core.exceptions import ConfigurationError
from felts.core.extractors.csv import CsvContract, CsvIdentity

CSV_IMPORT_SOURCE = "csv_import"
CONTRACTS_PATH = Path(__file__).with_name("contracts.yaml")
SUPPORTED_IDENTITY_STRATEGIES = {"filename_pattern", "value_column_header"}


def load_csv_contracts(path: Path = CONTRACTS_PATH) -> dict[str, CsvContract]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("contracts"), dict):
        msg = "CSV contracts file must contain a contracts mapping"
        raise ConfigurationError(msg)
    return {
        contract_id: _parse_contract(contract_id=contract_id, data=contract_data)
        for contract_id, contract_data in data["contracts"].items()
    }


def get_csv_contract(contract_id: str) -> CsvContract:
    contracts = load_csv_contracts()
    try:
        return contracts[contract_id]
    except KeyError as exc:
        msg = f"unsupported CSV contract: {contract_id}"
        raise ConfigurationError(msg) from exc


def _parse_contract(*, contract_id: str, data: Any) -> CsvContract:
    if not isinstance(data, dict):
        msg = f"{contract_id} CSV contract must be a mapping"
        raise ConfigurationError(msg)
    file_config = _mapping(data, "file", contract_id)
    identity_config = _mapping(data, "identity", contract_id)
    raw_record = _mapping(data, "raw_record", contract_id)
    schema = _mapping(data, "schema", contract_id)
    strategy = _string(identity_config, "strategy", contract_id)
    if strategy not in SUPPORTED_IDENTITY_STRATEGIES:
        msg = f"unsupported CSV identity strategy for {contract_id}: {strategy}"
        raise ConfigurationError(msg)
    return CsvContract(
        contract_id=contract_id,
        source=_string(data, "source", contract_id),
        entity=_string(data, "entity", contract_id),
        delimiter=_string(file_config, "delimiter", contract_id),
        encoding=_string(file_config, "encoding", contract_id),
        required_headers=tuple(_string_list(schema, "required_headers", contract_id)),
        allow_extra_headers=bool(schema.get("allow_extra_headers", False)),
        identity=CsvIdentity(
            strategy=strategy,
            pattern=cast(str | None, identity_config.get("pattern")),
            value_header_index=cast(int | None, identity_config.get("value_header_index")),
        ),
        source_record_id_fields=tuple(
            _string_list(raw_record, "source_record_id_fields", contract_id)
        ),
        observed_column=_string(raw_record, "observed_column", contract_id),
        dbt_selector=_string(data, "dbt_selector", contract_id),
    )


def _mapping(data: dict[str, Any], key: str, contract_id: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        msg = f"{contract_id}.{key} must be a mapping"
        raise ConfigurationError(msg)
    return value


def _string(data: dict[str, Any], key: str, contract_id: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        msg = f"{contract_id}.{key} must be a non-empty string"
        raise ConfigurationError(msg)
    return value


def _string_list(data: dict[str, Any], key: str, contract_id: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        msg = f"{contract_id}.{key} must be a string list"
        raise ConfigurationError(msg)
    return value

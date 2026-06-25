"""Generated Alphavantage REST extractor."""

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from itertools import product
from time import sleep
from typing import Any

from felts.core.exceptions import ExtractionError
from felts.core.extractors.base import BaseExtractor
from felts.core.extractors.rest import RestClient
from felts.core.schemas import ExtractedRecord
from felts.sources.alphavantage.constants import ALPHAVANTAGE_SOURCE, ENDPOINTS, Endpoint


class AlphavantageExtractor(BaseExtractor):
    def __init__(
        self,
        *,
        client: RestClient,
        api_key: str | None = None,
        request_interval_seconds: float = 2.0,
        sleep_fn: Any = sleep,
    ) -> None:
        if request_interval_seconds < 0:
            raise ExtractionError("request interval cannot be negative")
        self.client = client
        self.api_key = api_key
        self.request_interval_seconds = request_interval_seconds
        self.sleep = sleep_fn

    def extract(self) -> Iterable[ExtractedRecord]:
        for entity in ENDPOINTS:
            yield from self.extract_entity(entity)

    def extract_entity(
        self,
        entity: str,
        *,
        runtime_params: Mapping[str, Sequence[str]] | None = None,
    ) -> list[ExtractedRecord]:
        try:
            endpoint = ENDPOINTS[entity]
        except KeyError as exc:
            raise ExtractionError(f"unsupported Alphavantage entity: {entity}") from exc
        runtime_params = runtime_params or {}
        missing = [name for name in endpoint.runtime_params if not runtime_params.get(name)]
        if missing:
            raise ExtractionError(
                f"missing runtime parameter(s) for {entity}: {', '.join(missing)}"
            )
        names = endpoint.runtime_params
        values = [runtime_params[name] for name in names]
        combinations = tuple(product(*values)) if values else ((),)
        records: list[ExtractedRecord] = []
        for index, combination in enumerate(combinations):
            if index:
                self.sleep(self.request_interval_seconds)
            runtime_values = dict(zip(names, combination, strict=True))
            params = {
                **(endpoint.params or {}),
                **runtime_values,
            }
            if self.api_key:
                params["apikey"] = self.api_key
            data = self.client.get_json(endpoint.path, params=params)
            _raise_for_error_envelope(data)
            records.extend(
                _records_from_response(
                    entity=entity,
                    endpoint=endpoint,
                    data=data,
                    runtime_values=runtime_values,
                )
            )
        return records


def _records_from_response(
    *,
    entity: str,
    endpoint: Endpoint,
    data: Any,
    runtime_values: Mapping[str, str],
) -> list[ExtractedRecord]:
    if endpoint.response_shape == "list":
        if not isinstance(data, list):
            raise ExtractionError(f"{entity} response must be a list")
        payloads = [_object(entity, item) for item in data]
    elif endpoint.response_shape == "object":
        payloads = [_object(entity, data)]
    elif endpoint.response_shape == "data_object":
        top_level = _object(entity, data)
        payloads = [_object(entity, top_level.get("data"))]
    else:
        top_level = _object(entity, data)
        selected: Any = top_level
        for part in (endpoint.records_path or "").split("."):
            if not isinstance(selected, dict) or part not in selected:
                raise ExtractionError(
                    f"{entity} response is missing records path {endpoint.records_path!r}"
                )
            selected = selected[part]
        if not isinstance(selected, dict):
            raise ExtractionError(f"{entity} keyed response must select an object")
        payloads = []
        for key, value in selected.items():
            payload = _object(entity, value)
            payload[endpoint.key_field or "key"] = key
            payloads.append(payload)

    records = []
    for payload in payloads:
        payload.update(runtime_values)
        records.append(
            ExtractedRecord(
                source=ALPHAVANTAGE_SOURCE,
                entity=entity,
                payload=payload,
                source_record_id=_source_record_id(endpoint, payload),
            )
        )
    return records


def _raise_for_error_envelope(data: Any) -> None:
    if not isinstance(data, dict):
        return
    for key in ("Error Message", "Information", "Note"):
        if key in data:
            raise ExtractionError(f"Alpha Vantage response contained {key!r}")


def _source_record_id(endpoint: Endpoint, payload: Mapping[str, Any]) -> str | None:
    if not endpoint.id_fields:
        return None
    values = [payload.get(field) for field in endpoint.id_fields]
    if any(value is None for value in values):
        return None
    encoded = json.dumps(values, separators=(",", ":"), sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _object(entity: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExtractionError(f"{entity} response item must be an object")
    return dict(value)

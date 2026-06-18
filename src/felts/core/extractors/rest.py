"""Shared synchronous REST extraction helpers."""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import sleep
from typing import Any

import httpx

from felts.core.exceptions import ExtractionError

JsonObject = dict[str, Any]
JsonValue = JsonObject | list[Any]

RETRY_STATUSES = {429, 500, 502, 503, 504}


class RestClient:
    """Small synchronous JSON client with retry handling for extractors."""

    def __init__(
        self,
        *,
        base_url: str,
        headers: Mapping[str, str] | None = None,
        timeout_seconds: float = 30,
        retry_max_attempts: int = 3,
        retry_backoff_seconds: float = 0.5,
        sleep_fn: Callable[[float], None] = sleep,
        client: httpx.Client | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            msg = "timeout_seconds must be greater than zero"
            raise ExtractionError(msg)
        if retry_max_attempts < 1:
            msg = "retry_max_attempts must be at least one"
            raise ExtractionError(msg)
        if retry_backoff_seconds < 0:
            msg = "retry_backoff_seconds cannot be negative"
            raise ExtractionError(msg)

        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=dict(headers or {}),
            timeout=timeout_seconds,
        )
        self._owns_client = client is None
        self.retry_max_attempts: int = retry_max_attempts
        self.retry_backoff_seconds: float = retry_backoff_seconds
        self._sleep = sleep_fn

    def get_json(self, path: str, *, params: Mapping[str, Any] | None = None) -> JsonValue:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                response = self._client.get(path, params=params)
                if response.status_code in RETRY_STATUSES:
                    if attempt < self.retry_max_attempts:
                        self._sleep(self._retry_delay(response=response, attempt=attempt))
                        continue
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                break
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < self.retry_max_attempts and not isinstance(exc, ValueError):
                    self._sleep(self._retry_delay(response=None, attempt=attempt))
                    continue
                break
            else:
                if isinstance(data, dict | list):
                    return data
                msg = f"REST response for {path!r} must be a JSON object or array"
                raise ExtractionError(msg)

        msg = f"REST request failed for {path!r} after {self.retry_max_attempts} attempt(s)"
        if last_error is not None:
            msg = f"{msg}: {last_error}"
        raise ExtractionError(msg) from last_error

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "RestClient":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def _retry_delay(self, *, response: httpx.Response | None, attempt: int) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                parsed = _parse_retry_after(retry_after)
                if parsed is not None:
                    return parsed
        return float(self.retry_backoff_seconds * (2 ** (attempt - 1)))


def _parse_retry_after(value: str) -> float | None:
    if value.isdecimal():
        return float(value)
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None or retry_at.utcoffset() is None:
        retry_at = retry_at.replace(tzinfo=UTC)
    retry_timestamp = retry_at.timestamp()
    return max(retry_timestamp - datetime.now(UTC).timestamp(), 0.0)

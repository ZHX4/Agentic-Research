"""Shared HTTP transport with conservative rate limiting and retries."""

from __future__ import annotations

import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from time import monotonic

import httpx


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0


class RateLimiter:
    """Process-local minimum-interval limiter."""

    def __init__(self, min_interval_seconds: float) -> None:
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        self.min_interval_seconds = min_interval_seconds
        self._last_request_at: float | None = None

    def wait(self) -> None:
        now = monotonic()
        if self._last_request_at is not None:
            remaining = self.min_interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = monotonic()


class HttpClient:
    """Small synchronous HTTP client shared by all literature providers."""

    _RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

    def __init__(
        self,
        *,
        user_agent: str,
        timeout_seconds: float = 30.0,
        rate_limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
        transport: httpx.BaseTransport | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        request_headers = {"User-Agent": user_agent}
        if headers:
            request_headers.update(headers)
        self._client = httpx.Client(
            timeout=timeout_seconds,
            headers=request_headers,
            transport=transport,
            follow_redirects=True,
        )
        self._rate_limiter = rate_limiter or RateLimiter(0.0)
        self._retry = retry_policy or RetryPolicy()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get(self, url: str, *, params: dict[str, object] | None = None) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self._retry.max_attempts):
            self._rate_limiter.wait()
            try:
                response = self._client.get(url, params=params)
                if response.status_code not in self._RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    return response
                if attempt + 1 >= self._retry.max_attempts:
                    response.raise_for_status()
                delay = self._retry_delay(response, attempt)
                response.close()
                time.sleep(delay)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt + 1 >= self._retry.max_attempts:
                    break
                time.sleep(self._retry_delay(None, attempt))

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"HTTP request failed after {self._retry.max_attempts} attempts: {url}")

    def _retry_delay(self, response: httpx.Response | None, attempt: int) -> float:
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), self._retry.max_delay_seconds)
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(retry_after).timestamp()
                        return max(0.0, min(retry_at - time.time(), self._retry.max_delay_seconds))
                    except (TypeError, ValueError, OverflowError):
                        pass
        return min(self._retry.base_delay_seconds * (2**attempt), self._retry.max_delay_seconds)

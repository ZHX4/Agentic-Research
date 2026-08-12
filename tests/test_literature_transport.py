import httpx
import pytest

from agentic_research.literature.transport import HttpClient, RateLimiter, RetryPolicy


def test_rate_limiter_rejects_negative_interval() -> None:
    with pytest.raises(ValueError):
        RateLimiter(-1)


def test_http_client_retries_429(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    monkeypatch.setattr("agentic_research.literature.transport.time.sleep", lambda _: None)
    transport = httpx.MockTransport(handler)
    with HttpClient(
        user_agent="test",
        rate_limiter=RateLimiter(0),
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0, max_delay_seconds=0),
        transport=transport,
    ) as client:
        response = client.get("https://example.test")

    assert response.json() == {"ok": True}
    assert calls == 2


def test_http_client_raises_after_retryable_exhaustion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request)

    transport = httpx.MockTransport(handler)
    with pytest.raises(httpx.HTTPStatusError):
        with HttpClient(
            user_agent="test",
            rate_limiter=RateLimiter(0),
            retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0, max_delay_seconds=0),
            transport=transport,
        ) as client:
            client.get("https://example.test")

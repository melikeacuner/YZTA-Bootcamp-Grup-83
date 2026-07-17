from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.rate_limit import RateLimitMiddleware
from tests.fakes.fake_redis_counter import FakeRedisCounter


def _make_app(limit: int = 2) -> TestClient:
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    counter = FakeRedisCounter()
    app.add_middleware(
        RateLimitMiddleware,
        counter_client_factory=lambda: counter,
        limit=limit,
        window_seconds=60,
    )
    return TestClient(app)


def test_requests_within_limit_succeed():
    client = _make_app(limit=2)
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200


def test_request_over_limit_returns_429_with_retry_after():
    client = _make_app(limit=2)
    client.get("/ping")
    client.get("/ping")
    response = client.get("/ping")

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    body = response.json()
    assert body["status"] == "error"
    assert body["data"] is None


def test_rate_limiter_fails_open_when_counter_client_errors():
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    def broken_factory():
        raise ConnectionError("Redis erisilemedi")

    app.add_middleware(
        RateLimitMiddleware, counter_client_factory=broken_factory, limit=1, window_seconds=60
    )
    client = TestClient(app)

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200  # limit asilsa da fail-open ile gecer

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {"/health", "/ready", "/docs", "/openapi.json"}


class RateLimiter:
    """Sabit pencereli sayac: INCR + EXPIRE ile 60sn'de limit istegi asilirsa reddeder."""

    def __init__(self, limit: int = 100, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds

    async def check(self, counter_client, key: str) -> tuple[bool, int]:
        count = await counter_client.incr(key)
        if count == 1:
            await counter_client.expire(key, self.window_seconds)
        if count > self.limit:
            ttl = await counter_client.ttl(key)
            return False, max(ttl, 1)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis tabanli sabit pencere rate limiting; Redis erisilemezse fail-open davranir."""

    def __init__(
        self,
        app,
        counter_client_factory: Callable[[], object],
        limit: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self._counter_client_factory = counter_client_factory
        self._limiter = RateLimiter(limit, window_seconds)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_id = request.client.host if request.client else "anonymous"
        window = int(time.time()) // self._limiter.window_seconds
        key = f"ratelimit:{client_id}:{window}"

        try:
            counter_client = self._counter_client_factory()
            allowed, retry_after = await self._limiter.check(counter_client, key)
        except Exception:
            logger.warning("Rate limit kontrolu basarisiz, istek fail-open ile gecirildi", exc_info=True)
            return await call_next(request)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"status": "error", "data": None, "error": "Cok fazla istek gonderildi"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.rate_limit import RateLimitMiddleware
from app.api.routers.auth import router as auth_router
from app.api.routers.knowledge import router as knowledge_router
from app.api.routers.records import router as records_router
from app.api.routers.sessions import router as sessions_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.cache import redis_client as redis_client_module

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    description="Kurumsal problem çözme ve bilgi yönetimi platformu API'si.",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimitMiddleware,
    counter_client_factory=lambda: redis_client_module.create_redis_client(),
    limit=100,
    window_seconds=60,
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(sessions_router, prefix=settings.api_v1_prefix)
app.include_router(knowledge_router, prefix=settings.api_v1_prefix)
app.include_router(records_router, prefix=settings.api_v1_prefix)

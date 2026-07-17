from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe: süreç ayakta mı."""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness probe: bağımlılıklar hazır olunca genişletilecek (DB/Redis/Qdrant kontrolleri)."""
    return {"status": "ready"}

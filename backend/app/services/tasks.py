import time
import uuid

from app.core.config import get_settings
from app.infrastructure.celery_app import celery_app


@celery_app.task(name="embedding.process")
def process_embedding_task(record_id: str, text: str, payload: dict) -> bool:
    """Celery worker'i icinde calisan embedding + Qdrant upsert gorevi (maks. 3 deneme)."""
    from app.infrastructure.repositories.qdrant_repository import QdrantRepository
    from app.services.embedding_pipeline import EmbeddingPipeline
    from app.services.embedding_service import EmbeddingService

    settings = get_settings()
    pipeline = EmbeddingPipeline(EmbeddingService(), QdrantRepository())
    return pipeline.process(
        uuid.UUID(record_id),
        text,
        payload,
        sleep_fn=time.sleep,
        retry_interval=settings.embedding_retry_interval_seconds,
    )

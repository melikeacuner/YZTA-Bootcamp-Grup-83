import logging
import time
import uuid
from collections.abc import Callable

from app.core.config import get_settings
from app.infrastructure.repositories.qdrant_repository import QdrantRepository, QdrantUnavailableError
from app.services.embedding_service import EmbeddingService, EmbeddingUnavailableError

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Metni embed edip Qdrant'a yazan, hata durumunda sinirli sayida yeniden deneyen pipeline."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_repository: QdrantRepository,
        max_retries: int | None = None,
    ) -> None:
        settings = get_settings()
        self._embedding_service = embedding_service
        self._qdrant_repository = qdrant_repository
        self._max_retries = max_retries if max_retries is not None else settings.embedding_max_retries

    def process(
        self,
        record_id: uuid.UUID,
        text: str,
        payload: dict,
        sleep_fn: Callable[[float], None] = time.sleep,
        retry_interval: float = 0.0,
    ) -> bool:
        """Basariliysa True; max_retries denemesinden sonra hala basarisizsa False doner."""
        attempts = 0
        while attempts < self._max_retries:
            attempts += 1
            try:
                vector = self._embedding_service.embed(text)
                self._qdrant_repository.upsert(record_id, vector, payload)
                return True
            except (EmbeddingUnavailableError, QdrantUnavailableError) as exc:
                logger.warning("Embedding denemesi %s basarisiz: %s", attempts, exc)
                if attempts < self._max_retries and retry_interval > 0:
                    sleep_fn(retry_interval)
        return False

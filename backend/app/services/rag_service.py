import json
import logging
from typing import Protocol

from app.core.config import get_settings
from app.domain.validation import validate_search_query
from app.infrastructure.repositories.qdrant_repository import (
    QdrantRepository,
    QdrantUnavailableError,
    build_filter,
)
from app.services.embedding_service import EmbeddingService, EmbeddingUnavailableError

logger = logging.getLogger(__name__)


class DegradedModeError(Exception):
    """Qdrant/embedding erisilemedi; semantik arama gecici olarak devre disi (503)."""


class CacheClient(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ex: int) -> None: ...


class RAGSearchService:
    """Semantik arama: embedding uret, Qdrant'ta ara, sonucu Redis'te 300sn onbellekle."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_repository: QdrantRepository,
        cache: CacheClient | None = None,
    ) -> None:
        settings = get_settings()
        self._settings = settings
        self._embedding_service = embedding_service
        self._qdrant_repository = qdrant_repository
        self._cache = cache

    async def search(
        self,
        query: str,
        methodology: str | None = None,
        industry: str | None = None,
        department: str | None = None,
    ) -> list[dict]:
        validate_search_query(query)

        cache_key = self._cache_key(query, methodology, industry, department)
        if self._cache is not None:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return json.loads(cached)

        try:
            vector = self._embedding_service.embed(query)
            query_filter = build_filter(methodology=methodology, industry=industry, department=department)
            results = self._qdrant_repository.search(
                vector=vector,
                limit=self._settings.rag_max_results,
                score_threshold=self._settings.rag_similarity_threshold,
                query_filter=query_filter,
            )
        except (EmbeddingUnavailableError, QdrantUnavailableError) as exc:
            raise DegradedModeError(str(exc)) from exc

        payloads = [self._to_dict(point) for point in results]

        if self._cache is not None:
            await self._cache.set(
                cache_key, json.dumps(payloads), ex=self._settings.search_cache_ttl_seconds
            )

        return payloads

    @staticmethod
    def _to_dict(point) -> dict:
        return {"id": str(point.id), "score": point.score, **(point.payload or {})}

    @staticmethod
    def _cache_key(
        query: str, methodology: str | None, industry: str | None, department: str | None
    ) -> str:
        parts = json.dumps(
            {"q": query, "methodology": methodology, "industry": industry, "department": department},
            sort_keys=True,
        )
        return f"rag:search:{parts}"

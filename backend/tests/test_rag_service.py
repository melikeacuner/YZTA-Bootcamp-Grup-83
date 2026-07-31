import pytest

from app.services.embedding_service import EmbeddingService
from app.services.rag_service import DegradedModeError, RAGSearchService
from tests.fakes.fake_cache import FakeCache
from tests.fakes.fake_gemini_client import FakeGeminiClient
from tests.fakes.fake_qdrant_repository import FakeQdrantRepository, FakeScoredPoint

VALID_QUERY = "bant hattinda tekrarlayan duraksama"


@pytest.mark.asyncio
async def test_search_rejects_short_query():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    service = RAGSearchService(embedding_service, FakeQdrantRepository())

    with pytest.raises(ValueError):
        await service.search("kisa")


@pytest.mark.asyncio
async def test_search_returns_results_and_populates_cache():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository(
        search_results=[FakeScoredPoint(id="abc", score=0.8, payload={"title": "benzer vaka"})]
    )
    cache = FakeCache()
    service = RAGSearchService(embedding_service, qdrant_repo, cache=cache)

    results = await service.search(VALID_QUERY)

    assert len(results) == 1
    assert results[0]["title"] == "benzer vaka"
    assert results[0]["score"] == 0.8
    assert len(cache.set_calls) == 1


@pytest.mark.asyncio
async def test_search_returns_cached_results_without_calling_qdrant():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository(
        search_results=[FakeScoredPoint(id="abc", score=0.8, payload={"title": "ilk arama"})]
    )
    cache = FakeCache()
    service = RAGSearchService(embedding_service, qdrant_repo, cache=cache)

    await service.search(VALID_QUERY)
    qdrant_repo.search_results = [FakeScoredPoint(id="xyz", score=0.9, payload={"title": "ikinci arama"})]
    results = await service.search(VALID_QUERY)

    assert results[0]["title"] == "ilk arama"  # cache'ten geldi, qdrant tekrar cagrilmadi
    assert len(qdrant_repo.search_calls) == 1


@pytest.mark.asyncio
async def test_search_raises_degraded_mode_when_embedding_unavailable():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=False))
    service = RAGSearchService(embedding_service, FakeQdrantRepository())

    with pytest.raises(DegradedModeError):
        await service.search(VALID_QUERY)


@pytest.mark.asyncio
async def test_search_raises_degraded_mode_when_qdrant_unavailable():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository(always_fail=True)
    service = RAGSearchService(embedding_service, qdrant_repo)

    with pytest.raises(DegradedModeError):
        await service.search(VALID_QUERY)


@pytest.mark.asyncio
async def test_search_passes_filters_to_qdrant():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository(search_results=[])
    service = RAGSearchService(embedding_service, qdrant_repo)

    await service.search(VALID_QUERY, methodology="5why", industry="otomotiv")

    assert len(qdrant_repo.search_calls) == 1
    assert qdrant_repo.search_calls[0]["query_filter"] is not None

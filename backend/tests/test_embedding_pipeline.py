import uuid

from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.embedding_service import EmbeddingService
from tests.fakes.fake_gemini_client import FakeGeminiClient
from tests.fakes.fake_qdrant_repository import FakeQdrantRepository


def _noop_sleep(_seconds: float) -> None:
    return None


def test_pipeline_succeeds_on_first_attempt():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository()
    pipeline = EmbeddingPipeline(embedding_service, qdrant_repo, max_retries=3)

    ok = pipeline.process(uuid.uuid4(), "problem metni", {"title": "x"}, sleep_fn=_noop_sleep)

    assert ok is True
    assert len(qdrant_repo.upserted) == 1


def test_pipeline_retries_and_eventually_succeeds():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository(fail_times=2)
    pipeline = EmbeddingPipeline(embedding_service, qdrant_repo, max_retries=3)

    ok = pipeline.process(uuid.uuid4(), "problem metni", {}, sleep_fn=_noop_sleep, retry_interval=0.01)

    assert ok is True
    assert len(qdrant_repo.upserted) == 1


def test_pipeline_fails_after_max_retries():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=True))
    qdrant_repo = FakeQdrantRepository(always_fail=True)
    pipeline = EmbeddingPipeline(embedding_service, qdrant_repo, max_retries=3)

    ok = pipeline.process(uuid.uuid4(), "problem metni", {}, sleep_fn=_noop_sleep, retry_interval=0.01)

    assert ok is False
    assert len(qdrant_repo.upserted) == 0


def test_pipeline_fails_when_embedding_unavailable():
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=False))
    qdrant_repo = FakeQdrantRepository()
    pipeline = EmbeddingPipeline(embedding_service, qdrant_repo, max_retries=2)

    ok = pipeline.process(uuid.uuid4(), "problem metni", {}, sleep_fn=_noop_sleep)

    assert ok is False

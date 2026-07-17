import pytest

from app.services.embedding_service import EmbeddingService, EmbeddingUnavailableError
from tests.fakes.fake_gemini_client import FakeGeminiClient


def test_embed_raises_when_not_configured():
    client = FakeGeminiClient(configured=False)
    service = EmbeddingService(client=client)

    assert service.is_available is False
    with pytest.raises(EmbeddingUnavailableError):
        service.embed("bazi metin")


def test_embed_returns_vector_when_configured():
    client = FakeGeminiClient(configured=True, embedding_response=[0.1, 0.2, 0.3])
    service = EmbeddingService(client=client)

    vector = service.embed("bazi metin")

    assert vector == [0.1, 0.2, 0.3]
    assert client.embed_text_calls == ["bazi metin"]


def test_embed_wraps_client_errors():
    client = FakeGeminiClient(configured=True, raise_error=True)
    service = EmbeddingService(client=client)

    with pytest.raises(EmbeddingUnavailableError):
        service.embed("bazi metin")

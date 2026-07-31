from app.core.config import get_settings
from app.infrastructure.llm.gemini_client import GeminiClient


class EmbeddingUnavailableError(Exception):
    pass


class EmbeddingService:
    """Gemini embedding modeliyle metinleri vektorlere donusturur."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        settings = get_settings()
        self._client = client or GeminiClient(
            settings.gemini_api_key, settings.gemini_llm_model, settings.gemini_embedding_model
        )

    @property
    def is_available(self) -> bool:
        return self._client.is_configured

    def embed(self, text: str) -> list[float]:
        if not self.is_available:
            raise EmbeddingUnavailableError("GEMINI_API_KEY tanimli degil, embedding uretilemiyor")
        try:
            return self._client.embed_text(text)
        except Exception as exc:
            raise EmbeddingUnavailableError(str(exc)) from exc

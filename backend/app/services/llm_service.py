import asyncio
import logging

from app.core.config import get_settings
from app.infrastructure.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class LLMService:
    """Gemini ile metin uretimi; key yoksa/timeout/hata durumunda statik fallback'e doner."""

    def __init__(self, client: GeminiClient | None = None, timeout_seconds: float | None = None) -> None:
        settings = get_settings()
        self._timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.llm_timeout_seconds
        self._client = client or GeminiClient(
            settings.gemini_api_key, settings.gemini_llm_model, settings.gemini_embedding_model
        )

    @property
    def is_available(self) -> bool:
        return self._client.is_configured

    async def _generate_with_timeout(self, prompt: str) -> str:
        return await asyncio.wait_for(
            asyncio.to_thread(self._client.generate_text, prompt),
            timeout=self._timeout_seconds,
        )

    async def generate_follow_up_question(
        self, step_prompt: str, existing_answer: str, fallback: str
    ) -> str:
        if not self.is_available:
            return fallback

        prompt = (
            "Asagidaki adim icin kullanicinin yanitini netlestirecek, tek cumlelik kisa "
            f"bir takip sorusu uret.\nAdim: {step_prompt}\nKullanici yaniti: {existing_answer}"
        )
        try:
            text = await self._generate_with_timeout(prompt)
            return text.strip() or fallback
        except Exception:
            logger.warning("LLM takip sorusu uretimi basarisiz, statik sablona donuluyor", exc_info=True)
            return fallback

    async def summarize_problem(self, description: str, fallback: str | None = None) -> str:
        fallback_text = fallback if fallback is not None else description[:200]
        if not self.is_available:
            return fallback_text

        prompt = f"Asagidaki problemi 2-3 cumleyle ozetle:\n{description}"
        try:
            text = await self._generate_with_timeout(prompt)
            return text.strip() or fallback_text
        except Exception:
            logger.warning("LLM ozetleme basarisiz, orijinal metne donuluyor", exc_info=True)
            return fallback_text

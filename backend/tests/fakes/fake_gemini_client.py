import time


class FakeGeminiClient:
    """Testlerde gercek Gemini API'sine ihtiyac duymadan GeminiClient davranisini simule eder."""

    def __init__(
        self,
        configured: bool = True,
        text_response: str = "uretilen metin",
        embedding_response: list[float] | None = None,
        raise_error: bool = False,
        delay_seconds: float = 0.0,
    ) -> None:
        self._configured = configured
        self.text_response = text_response
        self.embedding_response = embedding_response or [0.1, 0.2, 0.3]
        self.raise_error = raise_error
        self.delay_seconds = delay_seconds
        self.generate_text_calls: list[str] = []
        self.embed_text_calls: list[str] = []

    @property
    def is_configured(self) -> bool:
        return self._configured

    def generate_text(self, prompt: str) -> str:
        self.generate_text_calls.append(prompt)
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.raise_error:
            raise RuntimeError("Gemini API hatasi")
        return self.text_response

    def embed_text(self, text: str) -> list[float]:
        self.embed_text_calls.append(text)
        if self.raise_error:
            raise RuntimeError("Gemini API hatasi")
        return self.embedding_response

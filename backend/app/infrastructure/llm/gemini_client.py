class GeminiClient:
    """google-generativeai SDK'sinin ince bir sarmalayicisi.

    NOT: gemini-1.5-flash ve text-embedding-004 Google tarafindan kullanimdan
    kaldirildi/kaldirilma surecinde. Gercek entegrasyon oncesi model adlarini
    (GEMINI_LLM_MODEL / GEMINI_EMBEDDING_MODEL env degiskenleri) guncel
    surumlerle degistirin - bkz. ai.google.dev/gemini-api/docs/deprecations.
    """

    def __init__(self, api_key: str | None, llm_model: str, embedding_model: str) -> None:
        self._api_key = api_key
        self._llm_model_name = llm_model
        self._embedding_model_name = embedding_model
        self._configured = False

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _ensure_configured(self) -> None:
        if self._configured:
            return
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        self._configured = True

    def generate_text(self, prompt: str) -> str:
        if not self.is_configured:
            raise RuntimeError("GEMINI_API_KEY tanimli degil")

        import google.generativeai as genai

        self._ensure_configured()
        model = genai.GenerativeModel(self._llm_model_name)
        response = model.generate_content(prompt)
        return response.text

    def embed_text(self, text: str) -> list[float]:
        if not self.is_configured:
            raise RuntimeError("GEMINI_API_KEY tanimli degil")

        import google.generativeai as genai

        self._ensure_configured()
        result = genai.embed_content(model=f"models/{self._embedding_model_name}", content=text)
        return list(result["embedding"])

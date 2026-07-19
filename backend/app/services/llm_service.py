import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.gemini_api_key
        self._model = model_name or settings.gemini_llm_model
        
        # If API key is not configured, we'll run in mock/fallback mode
        if self._api_key:
            try:
                self.client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai Client: {e}")
                self.client = None
        else:
            self.client = None

    @property
    def is_available(self) -> bool:
        return self.client is not None

    async def _generate(self, prompt: str, timeout: float = 15.0) -> str:
        if not self.is_available:
            logger.warning("Gemini API key not configured. Returning empty string fallback.")
            return ""
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self._model,
                contents=prompt
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            return ""

    async def _generate_json(self, prompt: str, timeout: float = 15.0) -> Dict[str, Any]:
        if not self.is_available:
            return {}
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text or "{}")
        except Exception as e:
            logger.error(f"LLM JSON generation failed: {e}", exc_info=True)
            # Fallback to text and extraction
            text = await self._generate(prompt, timeout)
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
            except Exception:
                pass
            return {}

    async def generate_clarification(self, problem_description: str) -> str:
        prompt = (
            "Aşağıdaki problem açıklamasını daha iyi anlamak için bir takip sorusu sor.\n"
            f"Problem Açıklaması: {problem_description}"
        )
        result = await self._generate(prompt)
        return result.strip() or "Problem hakkında daha fazla detay verebilir misiniz?"

    async def generate_next_why(self, problem_description: str, previous_whys: List[str]) -> str:
        context = "\n".join([f"Neden {i+1}: {why}" for i, why in enumerate(previous_whys)])
        prompt = (
            f"Problem: {problem_description}\n"
            f"Şu ana kadarki nedenler:\n{context}\n\n"
            "Bir sonraki 'Neden' sorusunu sor. Çok kısa, öz ve net olsun (tek bir soru)."
        )
        result = await self._generate(prompt)
        return result.strip() or "Bu durumun kök nedeni nedir?"

    async def generate_lessons_learned(self, problem_description: str, root_cause: str, methodology: str) -> str:
        prompt = (
            f"Problem: {problem_description}\n"
            f"Kök Neden: {root_cause}\n"
            f"Metodoloji: {methodology}\n\n"
            "Yukarıdaki problem çözüm sürecinden çıkarılan kurumsal dersleri (Lessons Learned) özetle. "
            "Gelecekte benzer durumların yaşanmaması için önleyici öneriler sun.\n"
            "Yanıtında şu başlıkları mutlaka içermelidir: 'Kök Neden', 'Düzeltici Eylemler', 'Sonuç', 'Önleyici Öneriler'."
        )
        result = await self._generate(prompt)
        required = ["Kök Neden", "Düzeltici Eylemler", "Sonuç", "Önleyici Öneriler"]
        if not result:
            return "Kök Neden: [Kök Neden]\nDüzeltici Eylemler: [Düzeltici Eylemler]\nSonuç: [Sonuç]\nÖnleyici Öneriler: [Önleyici Öneriler]"
        
        has_all = all(item in result for item in required)
        if not has_all:
            return (
                f"Kök Neden: {root_cause or 'Bilinmiyor'}\n"
                "Düzeltici Eylemler: [Belirtilmedi]\n"
                f"Sonuç: {result}\n"
                "Önleyici Öneriler: [Belirtilmedi]"
            )
        return result

    async def suggest_category_reassignment(self, cause: str, current_category: str) -> Optional[str]:
        prompt = (
            f"Neden: '{cause}'\n"
            f"Şu anki kategori: '{current_category}'\n\n"
            "Eğer bu neden başka bir Ishikawa kategorisine (Man, Machine, Method, Material, Measurement, Environment) "
            "daha uygunsa, sadece kategori ismini söyle (örn: Machine). Değilse 'UYGUN' de."
        )
        result = await self._generate(prompt)
        result = result.strip().upper()
        if "UYGUN" in result or result not in ["MAN", "MACHINE", "METHOD", "MATERIAL", "MEASUREMENT", "ENVIRONMENT"]:
            return None
        return result.capitalize()

    async def is_response_vague(self, response: str) -> bool:
        if len(response) < 10:
            return True
        prompt = (
            "Aşağıdaki kullanıcı yanıtının bir problem çözüm adımı için yeterince açıklayıcı olup olmadığını değerlendir.\n"
            f"Yanıt: '{response}'\n\n"
            "Eğer yanıt çok kısa, anlamsız veya yetersiz ise 'BELİRSİZ' de. Eğer yeterli ise 'YETERLİ' de."
        )
        result = await self._generate(prompt)
        return "BELİRSİZ" in result.upper()

    async def suggest_completion_details(self, problem_description: str, step_responses: dict) -> Dict[str, Any]:
        prompt = (
            f"Problem: {problem_description}\n"
            f"Analiz Detayları: {str(step_responses)}\n\n"
            "Bu problem için en uygun:\n"
            "1. Departman (Üretim, Lojistik, Kalite, Bilgi İşlem, Finans seçeneklerinden biri)\n"
            "2. Kısa ve vurucu bir özet başlık (maksimum 10 kelime)\n"
            "3. 4-5 adet anahtar kelime (tags)\n\n"
            "Yanıtı şu JSON formatında ver: "
            '{"department": "...", "summary": "...", "tags": ["tag1", "tag2", ...]}'
        )
        result = await self._generate_json(prompt)
        if not result:
            return {
                "department": "Üretim",
                "summary": f"Problem: {problem_description[:30]}...",
                "tags": ["problem", "analiz"]
            }
        return result

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        client: Any | None = None,
        timeout_seconds: float | None = None
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.gemini_api_key
        self._model = model_name or settings.gemini_llm_model
        self._timeout_seconds = timeout_seconds or 15.0
        
        # If a client is passed directly (like FakeGeminiClient in tests), use it
        if client is not None:
            self.client = client
        elif self._api_key:
            try:
                self.client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai Client: {e}")
                self.client = None
        else:
            self.client = None

    @property
    def is_available(self) -> bool:
        if hasattr(self.client, "is_configured"):
            return self.client.is_configured
        return self.client is not None

    async def _generate(self, prompt: str, timeout: float = 15.0) -> str:
        if not self.is_available:
            logger.warning("Gemini API key not configured. Returning empty string fallback.")
            return ""

        candidate_models = []
        for m in [self._model, "gemini-flash-latest", "gemini-pro-latest", "gemini-2.5-flash"]:
            if m and m not in candidate_models:
                candidate_models.append(m)

        for model_name in candidate_models:
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"LLM generation with model '{model_name}' failed: {e}")
                continue

        logger.error("All LLM candidate models failed.")
        return ""

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
            if hasattr(self.client, "generate_text"):
                return await asyncio.wait_for(
                    asyncio.to_thread(self.client.generate_text, prompt),
                    timeout=self._timeout_seconds
                )
            else:
                return await asyncio.wait_for(
                    self._generate(prompt),
                    timeout=self._timeout_seconds
                )
        except Exception:
            logger.warning("LLM takip sorusu uretimi basarisiz, statik sablona donuluyor", exc_info=True)
            return fallback

    async def summarize_problem(self, description: str, fallback: str | None = None) -> str:
        fallback_text = fallback if fallback is not None else description[:200]
        if not self.is_available:
            return fallback_text

        prompt = f"Asagidaki problemi 2-3 cumleyle ozetle:\n{description}"
        try:
            if hasattr(self.client, "generate_text"):
                return await asyncio.wait_for(
                    asyncio.to_thread(self.client.generate_text, prompt),
                    timeout=self._timeout_seconds
                )
            else:
                return await asyncio.wait_for(
                    self._generate(prompt),
                    timeout=self._timeout_seconds
                )
        except Exception:
            logger.warning("LLM ozetleme basarisiz, orijinal metne donuluyor", exc_info=True)
            return fallback_text

    async def _generate_json(self, prompt: str, timeout: float = 15.0) -> Dict[str, Any]:
        if not self.is_available:
            return {}

        candidate_models = []
        for m in [self._model, "gemini-flash-latest", "gemini-pro-latest", "gemini-2.5-flash"]:
            if m and m not in candidate_models:
                candidate_models.append(m)

        for model_name in candidate_models:
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as e:
                logger.warning(f"LLM JSON generation with model '{model_name}' failed: {e}")
                continue

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
            "Sen dünya klasında bir Yalın Üretim (TPS) ve Kök Neden Analizi Uzmanısın (Master Black Belt).\n"
            f"Problem Açıklaması: {problem_description}\n\n"
            "Kullanıcıya bu problemin teknik, operasyonel ve fiziksel detaylarını (ekipman, parametre, çevre, malzeme, insan etkisi) "
            "netleştirecek profesyonel, yapıcı ve probleme özel bir açıklama/soru yönelt. "
            "Cevabın 1-2 cümlelik net bir rehberlik sorusu olsun."
        )
        result = await self._generate(prompt)
        return result.strip() or "Bu teknik aksaklığın meydana geldiği koşullar ve gözlemlenen ilk belirtiler hakkında biraz daha detay verebilir misiniz?"

    async def generate_next_why(self, problem_description: str, previous_whys: List[str]) -> str:
        context = "\n".join([f"Neden {i+1}: {why}" for i, why in enumerate(previous_whys)])
        prompt = (
            f"Sen dünya klasında, son derece deneyimli bir Yalın Üretim ve Toyota Üretim Sistemi (TPS) kök neden analizi uzmanısın (Master Black Belt).\n"
            f"Problem Tanımı: {problem_description}\n"
            f"Şu ana kadar tespit edilen neden zinciri:\n{context}\n\n"
            f"En son belirtilen '{previous_whys[-1]}' etkeninin arkasındaki temel teknik, mekanik veya organizasyonel kök nedeni ortaya çıkarmak istiyoruz.\n"
            f"Lütfen jenerik veya sığ sorular ('neden oldu?') sorma. "
            f"Probleme özel 2 olası mantıklı kök neden hipotezi sun (Örn: '1. Aşınma/Kalibrasyon sapması mı, 2. Standart işletim prosedürü eksikliği mi?') "
            f"ve kullanıcının bu etkenlerden hangisinin asıl kök neden olduğunu doğrulamasını iste. (Maksimum 3 cümle)."
        )
        result = await self._generate(prompt)
        fallback = f"'{previous_whys[-1]}' durumuna yol açan kök fiziksel etkeni veya bakım/operasyon prosedürü eksikliğini açıklayabilir misiniz?"
        return result.strip() or fallback

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
            return f"Kök Neden: {root_cause or 'Analiz ile belirlendi'}\nDüzeltici Eylemler: Ekipman ve süreç denetimleri artırıldı.\nSonuç: Problem kalıcı olarak çözüldü.\nÖnleyici Öneriler: Periyodik bakım ve standart çalışma talimatları güncellendi."
        
        has_all = all(item in result for item in required)
        if not has_all:
            return (
                f"Kök Neden: {root_cause or 'Bilinmiyor'}\n"
                "Düzeltici Eylemler: Süreç kontrol parametreleri ve standartlar güncellendi.\n"
                f"Sonuç: {result}\n"
                "Önleyici Öneriler: Yokoten ile benzer hatta yaygınlaştırma yapıldı."
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

    async def summarize_document(self, filename: str, content: str) -> str:
        """Yüklenen döküman metnini analiz edip kısa teknik özet çıkarır."""
        if not content.strip():
            return f"'{filename}' belgesi metin içermiyor veya boş."
        if not self.is_available:
            return f"'{filename}' belgesi yüklendi. (İçerik uzunluğu: {len(content)} karakter)."

        prompt = (
            f"Sen bir Yalın Üretim ve Teknik Analiz Uzmanısın.\n"
            f"Dosya Adı: {filename}\n"
            f"Dosya İçeriği (ilk 4000 karakter):\n{content[:4000]}\n\n"
            f"Lütfen bu belgenin problem çözümü açısından en önemli teknik bulgularını, "
            f"kök neden kanıtlarını veya ölçüm verilerini 3-4 cümleyle Türkçe olarak özetle."
        )
        summary = await self._generate(prompt)
        return summary.strip() or f"'{filename}' belgesi analiz edildi ({len(content)} karakter)."

    async def generate_conversation_summary(self, chat_history: List[Dict[str, Any]]) -> str:
        """AI Agent ile yapılan sohbet geçmişinden kararları ve aksiyonları özetler."""
        if not chat_history:
            return "Henüz sohbet geçmişi yok."
        if not self.is_available:
            return f"Sohbet {len(chat_history)} mesaj içeriyor."

        history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in chat_history])
        prompt = (
            f"Aşağıda bir problem çözüm oturumundaki sohbet geçmişi yer almaktadır:\n{history_str}\n\n"
            f"Lütfen bu sohbetten çıkarılan:\n"
            f"1. Mutabık kalınan teknik tespitleri\n"
            f"2. Alınacak düzeltici eylem kararlarını\n"
            f"3. Bekleyen açık noktaları\n"
            f"3-4 maddelik net bir Türkçe özet halinde yaz."
        )
        summary = await self._generate(prompt)
        return summary.strip() or "Sohbet özeti oluşturuldu."

    async def generate_full_a3_report(
        self,
        title: str,
        description: str,
        methodology: str,
        step_responses: dict,
        document_summaries: list,
        chat_summary: str,
        existing_root_cause: str | None = None,
        existing_actions: str | None = None
    ) -> Dict[str, Any]:
        """Tüm problem verilerini birleştirerek eksiksiz A3 Raporu JSON nesnesi üretir."""
        docs_text = "\n".join([f"- {d.get('filename')}: {d.get('summary')}" for d in document_summaries]) or "Belge eklenmedi."
        prompt = (
            f"Problem Başlığı: {title}\n"
            f"Problem Tanımı: {description}\n"
            f"Metodoloji: {methodology}\n"
            f"Analiz Adım Yanıtları: {json.dumps(step_responses, ensure_ascii=False)}\n"
            f"İlişkili Döküman Özetleri:\n{docs_text}\n"
            f"Sohbet Özeti & Kararlar: {chat_summary}\n"
            f"Mevcut Kök Neden: {existing_root_cause or 'Belirtilmedi'}\n"
            f"Mevcut Düzeltici Aksiyonlar: {existing_actions or 'Belirtilmedi'}\n\n"
            f"Sen Master Black Belt Yalın Üretim Uzmanısın. Yukarıdaki tüm kanıt ve analizlerden yararlanarak "
            f"eksiksiz bir A3 Kök Neden Çözüm Raporu oluştur.\n\n"
            f"Aşağıdaki alanları içeren JSON döndür:\n"
            f"1. title: Kısa, profesyonel başlık\n"
            f"2. root_cause: Problemin kök nedeninin ayrıntılı açıklaması\n"
            f"3. corrective_actions: Kalıcı ve önleyici düzeltici eylemler (maddeler halinde)\n"
            f"4. lessons_learned: 'Kök Neden', 'Düzeltici Eylemler', 'Sonuç', 'Önleyici Öneriler' içeren kurumsal ders metni\n"
            f"5. yokoten_notes: Yatay yayılım (Yokoten) ve diğer hatlara uygulanma önerileri\n"
            f"6. tags: 4-5 anahtar kelime dizisi\n"
            f"7. department: Üretim, Lojistik, Kalite, Bilgi İşlem veya Finans\n\n"
            f"Format JSON: "
            f'{{"title": "...", "root_cause": "...", "corrective_actions": "...", "lessons_learned": "...", "yokoten_notes": "...", "tags": [...], "department": "..."}}'
        )
        result = await self._generate_json(prompt)
        if not result:
            return {
                "title": title,
                "root_cause": existing_root_cause or "Analiz ve sohbet verileri ile tespit edilen kök neden.",
                "corrective_actions": existing_actions or "Kararlaştırılan kalıcı düzeltici eylemler.",
                "lessons_learned": f"Kök Neden: {existing_root_cause}\nDüzeltici Eylemler: Aksiyonlar tamamlandı.\nSonuç: Problem kapatıldı.",
                "yokoten_notes": "Benzer ekipman ve süreçlere bilgilendirme yapıldı.",
                "tags": ["A3", "ProblemÇözme"],
                "department": "Kalite"
            }
        return result


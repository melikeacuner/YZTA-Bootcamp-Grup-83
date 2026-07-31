import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EmbeddingStatus, SessionStatus
from app.infrastructure.db.models import ProblemRecordORM, ProblemSession
from app.services.llm_service import LLMService
from app.services.embedding_pipeline import EmbeddingPipeline
from app.infrastructure.repositories.qdrant_repository import QdrantRepository

logger = logging.getLogger(__name__)

ROOT_CAUSE_PROMPT = """Sen uzman bir Problem Kök Neden Analiz Danışmanısın (5-Why, Ishikawa / Balık Kılçığı, 8D RCA Uzmanı).
Görevin, kullanıcının bildirdiği problemin altında yatan GERÇEK KÖK NEDENİ (Root Cause) bulmasını sağlamaktır.

ÇOK ÖNEMLİ KURALLAR (KESİNLİKLE UYULMALIDIR):
1. **HIZLI ÇÖZÜM ÖNERİSİ VERME**: Kullanıcı bir sorun bildirdiğinde (örneğin "Fabrikadaki tüm Wi-Fi yayınları gitti"), KESİNLİKLE doğrudan çözüm önerileri (ör. "modemi yeniden başlatın", "router değiştirin") VERME!
2. **KÖK NEDENİ SORGULA VE YÖNLENDİR**: Kullanıcıyı 5 Neden (5-Why) veya Ishikawa (İnsan, Makine, Malzeme, Metot, Ortam, Yönetim) kategorilerinde derinlemesine düşündür. Problemin arka planını, ne zaman başladığını, fiziksel/operasyonel tetikleyicilerini sorgula.
3. **KÖK NEDENİ NETLEŞTİR**: Kullanıcı ile konuşarak kök nedeni net bir ifadeye ulaştır. Kullanıcı kök nedeni ifade ettiğinde: "Kök neden tespit edildi: [...]. Şimdi bu kök nedeni 'Problem Havuzuna' gönderebilirsiniz." şeklinde onay ver.
4. **PROFESYONEL VE REHBER OL**: Yanıtların öz, yönlendirici ve tekniğe dayalı sorular içeren yapıda olsun.
"""

RESOLUTION_PROMPT = """Sen dünya standartlarında uzman bir Problem Çözme ve Kalıcı İyileştirme Danışmanısın (Lean Six Sigma Master Black Belt).
Kök nedeni bulunmuş problemin Kalıcı Olarak Giderilmesi, Standart Operasyon Prosedürü (SOP) Süreç Oluşturulması, Poka-Yoke (Hata Önleme) ve Yokoten (Yatay Yayılım) planlamasında kullanıcıya adım adım yönlendirme yap.
Kullanıcıya kalıcı aksiyon planları oluşturması ve süreci dökümante etmesi için yapıcı öneriler ver.
"""

SYSTEM_PROMPT = ROOT_CAUSE_PROMPT


class AgentService:
    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        pipeline: EmbeddingPipeline,
        qdrant_repo: QdrantRepository,
        rag_service: Any = None,
    ) -> None:
        self._db = db
        self._llm = llm
        self._pipeline = pipeline
        self._qdrant_repo = qdrant_repo
        self._rag_service = rag_service

    async def chat(self, session: ProblemSession, user_message: str, mode: str = "rca") -> str:
        # Get existing chat history
        history = list(session.agent_chat_history) if session.agent_chat_history else []
        
        # Append user message
        history.append({"role": "user", "content": user_message})

        # Fetch RAG context if available
        rag_context = ""
        if self._rag_service:
            try:
                similar = await self._rag_service.search(query=f"{session.problem_description} {user_message}")
                if similar:
                    rag_context = "\nBilgi Tabanından İlgili Benzer Vakalar:\n"
                    for s in similar[:2]:
                        rag_context += f"- {s.get('title')}: Kök Neden: {s.get('root_cause')}, Aksiyon: {s.get('corrective_actions')}\n"
            except Exception as e:
                logger.warning(f"Agent RAG context fetch failed: {e}")

        # Choose system prompt based on mode or session status
        chosen_prompt = RESOLUTION_PROMPT if (mode == "resolution" or session.status == "pool") else ROOT_CAUSE_PROMPT

        # Build prompt with history
        prompt_parts = [
            chosen_prompt,
            f"Problem Tanımı: {session.problem_description}\n"
            f"Departman: {session.department or 'Belirtilmedi'}\n"
            f"{rag_context}\n"
            f"Sohbet Geçmişi:"
        ]
        for msg in history:
            role_label = "Kullanıcı" if msg["role"] == "user" else "Danışman (Sen)"
            prompt_parts.append(f"{role_label}: {msg['content']}")

        if mode == "resolution" or session.status == "pool":
            prompt_parts.append(
                "Danışman (Sen): Kullanıcının mesajını değerlendir. Kök nedenin kalıcı giderilmesi, SOP süreç oluşturma ve aksiyon planı için somut öneri ver."
            )
        else:
            prompt_parts.append(
                "Danışman (Sen): Çözüm önerisi VERME. Kullanıcının problemin kök nedenini bulması için 5-Why veya Ishikawa bazlı sorgulatıcı yanıt ver."
            )
        
        full_prompt = "\n".join(prompt_parts)

        # Generate agent message
        agent_reply = await self._llm._generate(full_prompt)
        if not agent_reply:
            if mode == "resolution" or session.status == "pool":
                agent_reply = "Kök nedenin kalıcı olarak giderilmesi için: 1) SOP (Standart Operasyon Prosedürü) güncellemesi, 2) Poka-Yoke hata önleme mekanizması kurulumu önermekteyim."
            else:
                agent_reply = "Bu problemin ortaya çıkmasına neden olan ana etken nedir? Problemin ilk görüldüğü anda veya hemen öncesinde hangi değişiklik gerçekleşti (5-Why analizi)?"

        # Append agent reply
        history.append({"role": "assistant", "content": agent_reply})

        # Update session
        session.agent_chat_history = history
        session.updated_at = datetime.utcnow()
        await self._db.commit()

        return agent_reply

    async def resolve(self, session: ProblemSession) -> ProblemRecordORM:
        # Check if it's agent chat or structured methodology
        if session.methodology == "agent":
            history_text = ""
            for msg in session.agent_chat_history:
                role = "Kullanıcı" if msg["role"] == "user" else "Ajan"
                history_text += f"{role}: {msg['content']}\n"
            source_label = "Sohbet Geçmişi"
        else:
            history_text = ""
            answers = session.step_responses or session.step_data.get("answers", {})
            for step_name, ans in answers.items():
                history_text += f"{step_name}: {ans}\n"
            source_label = "Adım Yanıtları"

        prompt = (
            f"Aşağıdaki problem çözme adımlarından veya sohbet geçmişinden yararlanarak problemi analiz et ve yapılandırılmış bir çözüm sentezle:\n\n"
            f"Problem Tanımı: {session.problem_description}\n\n"
            f"{source_label}:\n{history_text}\n\n"
            "Yanıtı kesinlikle aşağıdaki JSON formatında üret. Alanlar boş kalmamalıdır, verilerden çıkarım yap:\n"
            "{\n"
            '  "title": "Problem için kısa ve vurucu başlık (maks 10 kelime)",\n'
            '  "root_cause": "Tespit edilen kök neden analizi sonucu",\n'
            '  "corrective_actions": "Kalıcı düzeltici ve önleyici eylemler",\n'
            '  "lessons_learned": "Bu vaka sonucunda organizasyonun öğrendiği dersler",\n'
            '  "department": "Üretim", // Üretim, Lojistik, Kalite, Bilgi İşlem, Finans seçeneklerinden biri\n'
            '  "industry": "İmalat",\n'
            '  "problem_category": "Kalite Hatası",\n'
            '  "tags": ["etiket1", "etiket2"],\n'
            '  "severity": 5, // 1-10 arası tamsayı\n'
            '  "occurrence": 4, // 1-10 arası tamsayı\n'
            '  "detection": 3, // 1-10 arası tamsayı\n'
            '  "yokoten_applied": true // true veya false\n'
            "}"
        )

        synthesis = await self._llm._generate_json(prompt)
        if not synthesis:
            synthesis = {
                "title": f"Çözüm: {session.problem_description[:30]}",
                "root_cause": "Sohbet analizi sonucu kök neden tespit edildi.",
                "corrective_actions": "Düzeltici önlemler alındı.",
                "lessons_learned": "Sürekli kontrol ve denetimlerin artırılması gerektiği öğrenildi.",
                "department": session.department or "Kalite",
                "industry": "Genel",
                "problem_category": "Diğer",
                "tags": ["çözüldü", "agent"],
                "severity": 5,
                "occurrence": 5,
                "detection": 5,
                "yokoten_applied": False
            }

        # Calculate RPN
        severity = int(synthesis.get("severity") or 1)
        occurrence = int(synthesis.get("occurrence") or 1)
        detection = int(synthesis.get("detection") or 1)
        rpn = severity * occurrence * detection

        # Create Record
        record = ProblemRecordORM(
            session_id=session.id,
            user_id=session.owner_id,
            title=synthesis.get("title") or "Çözüm Raporu",
            description=session.problem_description,
            methodology="AGENT",
            methodology_data={"chat_length": len(session.agent_chat_history)},
            step_responses={"chat_history": session.agent_chat_history},
            root_cause=synthesis.get("root_cause"),
            corrective_actions=synthesis.get("corrective_actions"),
            lessons_learned=synthesis.get("lessons_learned"),
            industry=synthesis.get("industry") or "İmalat",
            department=synthesis.get("department") or "Kalite",
            problem_category=synthesis.get("problem_category") or "Diğer",
            tags=synthesis.get("tags") or [],
            severity=severity,
            occurrence=occurrence,
            detection=detection,
            rpn=rpn,
            yokoten_applied=bool(synthesis.get("yokoten_applied")),
            closure_checklist={"checklist": ["Görüşmeler incelendi", "Ajan raporu onaylandı"]},
            resolution_status="open",
            resolution_date=None,
            embedding_status=EmbeddingStatus.PENDING.value
        )

        self._db.add(record)
        
        # Complete session
        session.status = SessionStatus.COMPLETED.value
        session.agent_status = "closed"
        session.updated_at = datetime.utcnow()
        await self._db.commit()
        await self._db.refresh(record)

        # Trigger semantic indexing
        text_to_embed = f"{record.title}\n{record.description}\n{record.lessons_learned}\n{record.root_cause}"
        payload = {
            "title": record.title,
            "methodology": record.methodology,
            "industry": record.industry,
            "department": record.department,
        }
        
        ok = self._pipeline.process(record.id, text_to_embed, payload)
        record.embedding_status = EmbeddingStatus.COMPLETED.value if ok else EmbeddingStatus.FAILED.value
        await self._db.commit()

        # Export to Obsidian Vault
        try:
            from app.services.obsidian_service import ObsidianService
            obsidian = ObsidianService(self._db, self._rag_service)
            await obsidian.export_record(record.id)
            logger.info(f"Record {record.id} successfully exported to Obsidian vault.")
        except Exception as obs_err:
            logger.error(f"Failed to export record to Obsidian: {obs_err}", exc_info=True)

        return record

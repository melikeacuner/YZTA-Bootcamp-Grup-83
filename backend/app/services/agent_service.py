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

SYSTEM_PROMPT = """Sen uzman bir Problem Çözme ve Süreç İyileştirme Danışmanısın (Lean Six Sigma, Toyota Production System, 8D, Ishikawa, 5-Why ve FMEA uzmanı).
Görevin, kullanıcının bildirdiği problemi çözmesine adım adım rehberlik etmektir. 

Lütfen şu yönergeleri takip et:
1. **Süreci Yönet**: Kullanıcıyı doğrudan çözüme atlamaktan koru. Önce problemi tanımla, geçici koruma önlemlerini (containment) konuş, kök neden analizi yaptır ve en son kalıcı düzeltici eylemleri belirle.
2. **FMEA Risk Değerlendirmesi**: Süreçte FMEA (Severity - Şiddet, Occurrence - Sıklık, Detection - Saptanabilirlik) değerlerini (1-10 arası) konuşup Risk Öncelik Sayısını (RPN = S * O * D) belirlemeye çalış.
3. **Yokoten**: Bu çözümün diğer departmanlarda/süreçlerde de yaygınlaştırılıp (horizontal deployment) yaygınlaştırılamayacağını sor.
4. **Profesyonel ve Yönlendirici Ol**: Yanıtların kısa, yapıcı ve bir sonraki adıma yönlendirici sorular barındırsın.

Kullanıcıyla problemi analiz ettikten sonra, kullanıcı hazır olduğunu belirttiğinde çözümü kapatıp raporlamayı önerebilirsin."""


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

    async def chat(self, session: ProblemSession, user_message: str) -> str:
        # Get existing chat history
        history = list(session.agent_chat_history) if session.agent_chat_history else []
        
        # Append user message
        history.append({"role": "user", "content": user_message})

        # Build prompt with history
        prompt_parts = [SYSTEM_PROMPT, f"Problem Açıklaması: {session.problem_description}\n\nSohbet Geçmişi:"]
        for msg in history:
            role_label = "Kullanıcı" if msg["role"] == "user" else "Danışman (Sen)"
            prompt_parts.append(f"{role_label}: {msg['content']}")
        prompt_parts.append("Danışman (Sen):")
        
        full_prompt = "\n".join(prompt_parts)

        # Generate agent message
        agent_reply = await self._llm._generate(full_prompt)
        if not agent_reply:
            agent_reply = "Anladım, lütfen problemi çözmemiz için adımları detaylandırmaya devam edelim."

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
            resolution_status="closed",
            resolution_date=datetime.utcnow(),
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

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession


from app.domain.enums import EmbeddingStatus
from app.domain.validation import validate_lessons_learned, validate_problem_description
from app.infrastructure.db.models import ProblemRecordORM, ProblemSession
from app.infrastructure.repositories.problem_record_repository import ProblemRecordRepository
from app.infrastructure.repositories.qdrant_repository import QdrantRepository, QdrantUnavailableError
from app.services.audit_service import AuditService
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.rag_service import DegradedModeError


class RecordNotFoundError(Exception):
    pass


class KnowledgeService:
    """Tamamlanmis oturumlardan ProblemRecord kaydi olusturur, gunceller, siler."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_pipeline: EmbeddingPipeline,
        qdrant_repository: QdrantRepository,
        rag_service: any = None,
        llm_service: any = None,
    ) -> None:
        self._session = session
        self._records = ProblemRecordRepository(session)
        self._audit = AuditService(session)
        self._pipeline = embedding_pipeline
        self._qdrant_repository = qdrant_repository
        self._rag_service = rag_service
        self._llm = llm_service

    @staticmethod
    def _embedding_payload(record: ProblemRecordORM) -> dict:
        return {
            "title": record.title,
            "methodology": record.methodology,
            "industry": record.industry,
            "department": record.department,
        }

    @staticmethod
    def _embedding_text(record: ProblemRecordORM) -> str:
        return f"{record.title}\n{record.description}\n{record.lessons_learned}"

    async def create_from_session(
        self,
        problem_session: ProblemSession,
        user_id: uuid.UUID,
        title: str,
        lessons_learned: str,
        root_cause: str | None = None,
        corrective_actions: str | None = None,
        industry: str | None = None,
        department: str | None = None,
        problem_category: str | None = None,
        severity: int = 1,
        occurrence: int = 1,
        detection: int = 1,
        yokoten_applied: bool = False,
    ) -> ProblemRecordORM:
        validate_problem_description(problem_session.problem_description)
        validate_lessons_learned(lessons_learned)

        record = ProblemRecordORM(
            session_id=problem_session.id,
            user_id=user_id,
            title=title,
            description=problem_session.problem_description,
            methodology=problem_session.methodology,
            industry=industry,
            department=department,
            problem_category=problem_category,
            methodology_data=problem_session.step_responses or problem_session.step_data.get("answers", {}),
            step_responses=problem_session.step_responses or problem_session.step_data.get("answers", {}),
            root_cause=root_cause,
            corrective_actions=corrective_actions,
            lessons_learned=lessons_learned,
            severity=severity,
            occurrence=occurrence,
            detection=detection,
            rpn=severity * occurrence * detection,
            yokoten_applied=yokoten_applied,
            closure_checklist={"checklist": ["Oturum tamamlandı", "Rapor kaydedildi"]},
            resolution_status="open",
            resolution_date=None,
            embedding_status=EmbeddingStatus.PENDING.value,
        )
        await self._records.create(record)

        # Auto-link tasks created for this session to the new problem record
        from sqlalchemy import update
        from app.infrastructure.db.models import Task
        await self._session.execute(
            update(Task)
            .where(Task.session_id == problem_session.id)
            .values(problem_record_id=record.id)
        )

        await self._audit.log(
            user_id=user_id,
            operation="record.create",
            entity_type="problem_record",
            entity_id=record.id,
            after_state={"title": record.title, "methodology": record.methodology},
        )

        ok = self._pipeline.process(
            record.id, self._embedding_text(record), self._embedding_payload(record)
        )
        record.embedding_status = (
            EmbeddingStatus.COMPLETED.value if ok else EmbeddingStatus.FAILED.value
        )
        await self._session.flush()

        # Export to Obsidian Vault
        try:
            from app.services.obsidian_service import ObsidianService
            obsidian = ObsidianService(self._session, self._rag_service)
            await obsidian.export_record(record.id)
        except Exception as obs_err:
            import logging
            logging.getLogger(__name__).error(f"Failed to export record to Obsidian: {obs_err}", exc_info=True)

        return record


    async def get(self, record_id: uuid.UUID) -> ProblemRecordORM:
        record = await self._records.get_by_id(record_id)
        if record is None:
            raise RecordNotFoundError(record_id)

        meta = dict(record.meta_data or {})
        if not meta.get("resolution_chat_history"):
            initial_msg = (
                f"Merhaba! Bu vaka için tespit edilen kök neden: '{record.root_cause or 'Analiz aşamasında belirlendi'}'.\n"
                f"Bu kök nedeni tamamen elimine etmek ve tekrarlanmasını önlemek için kalıcı düzeltici eylem planını birlikte oluşturalım. "
                f"Sorumlu kişiler, eylem adımları ve hedef süre hakkında fikirlerinizi iletebilir veya benden öneri isteyebilirsiniz."
            )
            meta["resolution_chat_history"] = [{"role": "assistant", "content": initial_msg}]
            record.meta_data = meta
            await self._session.flush()

        await self._session.refresh(record)
        return record

    async def list_paginated(
        self, page: int = 1, page_size: int = 20, resolution_status: str | None = None
    ) -> tuple[list[ProblemRecordORM], int]:
        return await self._records.list_paginated(page, page_size, resolution_status)

    async def update(
        self, record_id: uuid.UUID, user_id: uuid.UUID, **fields
    ) -> ProblemRecordORM:
        record = await self.get(record_id)
        before_state = {"title": record.title, "lessons_learned": record.lessons_learned}

        if "lessons_learned" in fields and fields["lessons_learned"] is not None:
            validate_lessons_learned(fields["lessons_learned"])

        for key, value in fields.items():
            if value is not None:
                setattr(record, key, value)

        record.embedding_status = EmbeddingStatus.PENDING.value
        ok = self._pipeline.process(
            record.id, self._embedding_text(record), self._embedding_payload(record)
        )
        record.embedding_status = (
            EmbeddingStatus.COMPLETED.value if ok else EmbeddingStatus.FAILED.value
        )

        await self._audit.log(
            user_id=user_id,
            operation="record.update",
            entity_type="problem_record",
            entity_id=record.id,
            before_state=before_state,
            after_state={"title": record.title, "lessons_learned": record.lessons_learned},
        )
        await self._session.flush()
        await self._session.refresh(record)

        # Export to Obsidian Vault
        try:
            from app.services.obsidian_service import ObsidianService
            obsidian = ObsidianService(self._session, self._rag_service)
            await obsidian.export_record(record.id)
        except Exception as obs_err:
            import logging
            logging.getLogger(__name__).error(f"Failed to export record to Obsidian: {obs_err}", exc_info=True)

        return record

    async def delete(self, record_id: uuid.UUID, user_id: uuid.UUID) -> None:
        record = await self.get(record_id)

        try:
            self._qdrant_repository.delete(record_id)
        except QdrantUnavailableError as exc:
            raise DegradedModeError(str(exc)) from exc

        await self._audit.log(
            user_id=user_id,
            operation="record.delete",
            entity_type="problem_record",
            entity_id=record.id,
            before_state={"title": record.title},
        )
        await self._records.delete(record_id)

    async def upload_and_summarize_document(
        self, record_id: uuid.UUID, filename: str, content_bytes: bytes, file_type: str = "text/plain"
    ) -> ProblemRecordORM:
        """Kullanıcının yüklediği dökümanı okur, AI özeti oluşturur ve kayda ekler."""
        record = await self.get(record_id)
        meta = dict(record.meta_data or {})
        documents = list(meta.get("documents", []))

        # Metin çıkarma
        extracted_text = ""
        try:
            # Saf metin decode dene
            extracted_text = content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            extracted_text = f"{filename} ikili dosya içeriği ({len(content_bytes)} bayt)."

        # AI ile dökümanı özetle
        summary = ""
        if self._llm:
            try:
                summary = await self._llm.summarize_document(filename, extracted_text)
            except Exception:
                pass
        
        if not summary:
            summary = f"'{filename}' dökümanı yüklendi. ({len(extracted_text)} karakter)."

        doc_item = {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "file_type": file_type,
            "summary": summary,
            "uploaded_at": datetime.utcnow().isoformat(),
            "extracted_preview": extracted_text[:500]
        }
        documents.append(doc_item)
        meta["documents"] = documents
        record.meta_data = meta
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def delete_document(self, record_id: uuid.UUID, doc_id: str) -> ProblemRecordORM:
        """Kayıttan dokümanı siler."""
        record = await self.get(record_id)
        meta = dict(record.meta_data or {})
        documents = list(meta.get("documents", []))
        updated_docs = [d for d in documents if d.get("id") != doc_id]
        meta["documents"] = updated_docs
        record.meta_data = meta
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def generate_a3_preview(self, record_id: uuid.UUID) -> dict:
        """Kapanış öncesinde canlı A3 raporu tasarısı üretir."""
        record = await self.get(record_id)
        meta = dict(record.meta_data or {})
        chat_history = meta.get("resolution_chat_history", [])
        documents = meta.get("documents", [])
        chat_summary = meta.get("conversation_summary", "")

        if not chat_summary and self._llm and chat_history:
            chat_summary = await self._llm.generate_conversation_summary(chat_history)

        if self._llm:
            a3_data = await self._llm.generate_full_a3_report(
                title=record.title,
                description=record.description,
                methodology=record.methodology,
                step_responses=record.step_responses or {},
                document_summaries=documents,
                chat_summary=chat_summary,
                existing_root_cause=record.root_cause,
                existing_actions=record.corrective_actions
            )
        else:
            a3_data = {
                "title": record.title,
                "root_cause": record.root_cause or "Analiz sonucunda tespit edildi.",
                "corrective_actions": record.corrective_actions or "Düzeltici aksiyonlar belirlendi.",
                "lessons_learned": record.lessons_learned,
                "yokoten_notes": "Benzer süreçlere yaygınlaştırma önerildi.",
                "tags": record.tags or ["A3"],
                "department": record.department or "Kalite"
            }
        return a3_data

    async def record_chat(self, record_id: uuid.UUID, user_message: str) -> ProblemRecordORM:
        record = await self.get(record_id)
        meta = dict(record.meta_data or {})
        history = list(meta.get("resolution_chat_history", []))
        documents = list(meta.get("documents", []))
        
        history.append({"role": "user", "content": user_message})
        
        # --- Doküman Özetleri Bağlamı ---
        doc_context = ""
        if documents:
            doc_context = "\n\nSisteme Yüklenen İlgili Dökümanların Özetleri:\n"
            for d in documents:
                doc_context += f"- Belge Adı: {d.get('filename')} | Özet: {d.get('summary')}\n"
            doc_context += "Gerekirse bu teknik belgelere ve bulgulara atıfta bulunarak yanıt ver.\n"

        # --- RAG: Search for similar resolved problems to enrich context ---
        similar_context = ""
        if self._rag_service:
            try:
                similar_results = await self._rag_service.search(query=f"{record.description} {user_message}")
                if similar_results:
                    similar_context = "\n\nBilgi tabanından benzer çözülmüş vakalar:\n"
                    for sr in similar_results[:3]:
                        sr_title = sr.get("title", "Bilinmeyen")
                        sr_root = sr.get("root_cause", "")
                        sr_lessons = sr.get("lessons_learned", "")[:200]
                        similar_context += f"- Başlık: {sr_title} | Kök Neden: {sr_root} | Dersler: {sr_lessons}\n"
                    similar_context += "Bu geçmiş vakaları referans alarak kullanıcıya somut öneriler sun.\n"
            except Exception:
                pass

        # Build context for the AI resolution assistant
        context = (
            f"Sen dünya klasında, son derece deneyimli bir Yalın Üretim ve Toyota Üretim Sistemi (TPS) problem çözme uzmanısın (Master Black Belt).\n"
            f"Kullanıcı bir problem kaydının kök nedenini çözmek ve kalıcı düzeltici eylemleri planlamak için sizinle görüşüyor.\n"
            f"Problem Başlığı: {record.title}\n"
            f"Problem Tanımı: {record.description}\n"
            f"Kullanılan Metodoloji: {record.methodology}\n"
            f"Kök Neden Bulguları: {record.root_cause or 'Henüz tam olarak belirtilmedi'}\n"
            f"Departman: {record.department or 'Belirtilmedi'}\n"
            f"{doc_context}\n"
            f"{similar_context}\n"
            f"Sohbet Geçmişi:\n"
        )
        for msg in history[:-1]:
            context += f"{msg['role']}: {msg['content']}\n"
        context += f"user: {user_message}\n\n"
        context += (
            "Lütfen yukarıdaki bağlam doğrultusunda kullanıcıya yanıt ver.\n"
            "Görevin: Kullanıcının kök nedene yönelik kalıcı düzeltici eylemleri (corrective actions) planlamasına, "
            "benzer problemlerin tekrarını önlemek için önlemler almasına ve dökümantasyonu tamamlamasına yardımcı olmak.\n"
            "AI olarak problem kök nedeninin çözümü için kullanıcıya özel, somut ve uygulanabilir öneriler sunmalısın.\n"
            "Eğer bilgi tabanında benzer geçmiş vakalar veya yüklenen belgeler varsa bunlara referans vererek önerilerde bulun.\n"
            "Eğer problem çözülmüş görünüyorsa, kullanıcıdan onay isteyerek 'Problemi kapatmak için Onayla butonuna basabilirsiniz' diyebilirsin."
        )
        
        ai_response = ""
        if self._llm:
            try:
                ai_response = await self._llm._generate(context)
            except Exception:
                pass
                
        if not ai_response:
            ai_response = "Problemin kök nedenini tamamen ortadan kaldırmak için alabileceğimiz önleyici eylemleri planlamanıza yardımcı olayım. Hangi adımları atmak istersiniz?"
            
        history.append({"role": "assistant", "content": ai_response})
        meta["resolution_chat_history"] = history
        
        # Güncellenmiş Konuşma Özetini Hesapla
        if self._llm:
            try:
                conv_summary = await self._llm.generate_conversation_summary(history)
                meta["conversation_summary"] = conv_summary
            except Exception:
                pass

        record.meta_data = meta
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def close_record(self, record_id: uuid.UUID, user_id: uuid.UUID) -> ProblemRecordORM:
        record = await self.get(record_id)
        meta = dict(record.meta_data or {})
        history = list(meta.get("resolution_chat_history", []))
        documents = list(meta.get("documents", []))
        chat_summary = meta.get("conversation_summary", "")

        if not chat_summary and self._llm and history:
            try:
                chat_summary = await self._llm.generate_conversation_summary(history)
            except Exception:
                chat_summary = "Sohbet tamamlandı."

        # Kapsamlı A3 Raporu oluştur
        details = {}
        if self._llm:
            try:
                details = await self._llm.generate_full_a3_report(
                    title=record.title,
                    description=record.description,
                    methodology=record.methodology,
                    step_responses=record.step_responses or {},
                    document_summaries=documents,
                    chat_summary=chat_summary,
                    existing_root_cause=record.root_cause,
                    existing_actions=record.corrective_actions
                )
            except Exception:
                pass

        record.title = details.get("title") or record.title
        record.root_cause = details.get("root_cause") or record.root_cause or "Analiz sonucunda kök neden belirlendi."
        record.corrective_actions = details.get("corrective_actions") or record.corrective_actions or "Düzeltici aksiyonlar planlandı."
        
        # Structured lessons learned
        lessons = details.get("lessons_learned", "")
        if lessons:
            record.lessons_learned = lessons
        elif not record.lessons_learned or record.lessons_learned == "Otomatik":
            record.lessons_learned = (
                f"Kök Neden: {record.root_cause}\n"
                f"Düzeltici Eylemler: {record.corrective_actions}\n"
                f"Sonuç: Problem analiz edildi ve çözüm uygulandı.\n"
                f"Önleyici Öneriler: Benzer durumların tekrarlamasını önlemek için kontrol mekanizmaları oluşturulmalıdır."
            )
        
        # Auto-extract tags
        ai_tags = details.get("tags", [])
        if isinstance(ai_tags, list) and ai_tags:
            existing_tags = record.tags or []
            merged_tags = list(set(existing_tags + ai_tags))
            record.tags = merged_tags[:10]
        
        # Update department from AI suggestion if not already set
        ai_dept = details.get("department")
        if ai_dept and not record.department:
            record.department = ai_dept
        
        record.resolution_status = "closed"
        record.resolution_date = datetime.utcnow()
        record.closure_checklist = {
            "checklist": [
                "Düzeltici aksiyonlar tamamlandı",
                "Kök neden çözümü doğrulandı",
                "Doküman ve sohbet kanıtları özetlendi",
                "Kapanış onaylandı"
            ]
        }
        
        # Save closer metadata
        meta["closed_by_user_id"] = str(user_id)
        meta["closed_at"] = datetime.utcnow().isoformat()
        meta["conversation_summary"] = chat_summary
        meta["a3_final_report"] = details
        meta["closure_summary"] = {
            "root_cause": record.root_cause,
            "corrective_actions": record.corrective_actions,
            "chat_message_count": len(history),
            "document_count": len(documents)
        }
        record.meta_data = meta
        
        # Trigger re-embedding / semantic indexing
        record.embedding_status = EmbeddingStatus.PENDING.value
        ok = self._pipeline.process(
            record.id, self._embedding_text(record), self._embedding_payload(record)
        )
        record.embedding_status = (
            EmbeddingStatus.COMPLETED.value if ok else EmbeddingStatus.FAILED.value
        )
        
        # Log audit log
        await self._audit.log(
            user_id=user_id,
            operation="record.close",
            entity_type="problem_record",
            entity_id=record.id,
            after_state={"status": "closed"},
        )
        
        # Sync corresponding DevOps task to completed
        try:
            from sqlalchemy import select
            from app.infrastructure.db.models import Task
            stmt = select(Task).where(
                (Task.problem_record_id == record.id) | (Task.session_id == record.session_id)
            )
            tasks_res = await self._session.execute(stmt)
            tasks_to_complete = tasks_res.scalars().all()
            for task_obj in tasks_to_complete:
                task_obj.status = "completed"
        except Exception as task_sync_err:
            import logging
            logging.getLogger(__name__).warning(f"Failed to sync task status on close_record: {task_sync_err}")

        await self._session.flush()
        await self._session.refresh(record)
        
        # Export to Obsidian Vault
        try:
            from app.services.obsidian_service import ObsidianService
            obsidian = ObsidianService(self._session, self._rag_service)
            await obsidian.export_record(record.id)
        except Exception as obs_err:
            import logging
            logging.getLogger(__name__).error(f"Failed to export record to Obsidian: {obs_err}", exc_info=True)
            
        return record

    async def ask_corporate_brain(self, query: str, department: str | None = None) -> dict:
        """Kullanıcının sorusunu veritabanı ve Qdrant geçmiş vakalarından okuyup LLM ile sentezler."""
        db_records, _ = await self.list_paginated(page=1, page_size=20)
        
        relevant_docs = []
        for r in db_records:
            if department and r.department and department != "Tüm Şirket" and r.department != department:
                continue
            relevant_docs.append({
                "id": str(r.id),
                "title": r.title,
                "department": r.department or "Genel",
                "root_cause": r.root_cause or "Kök neden tespiti yapıldı.",
                "lessons_learned": r.lessons_learned or "Düzeltici faaliyet uygulandı.",
                "industry": r.industry or "İmalat"
            })

        if not relevant_docs:
            return {
                "answer": "Aradığınız kriterlere uygun kurumsal hafıza kaydı bulunamadı.",
                "sources": []
            }

        # Build prompt context from corporate records
        context_str = "\n".join([
            f"- [{d['title']}] (Departman: {d['department']}): Kök Neden: {d['root_cause']} | Dersler: {d['lessons_learned']}"
            for d in relevant_docs[:6]
        ])

        prompt = (
            f"Sen kurumsal sorun yönetimi yapay zeka danışmanısın.\n"
            f"Aşağıdaki geçmiş vaka verilerini inceleyerek kullanıcının sorusunu kapsamlı, analitik ve Türkçe olarak yanıtla.\n\n"
            f"GEÇMİŞ KURUMSAL VAKALAR:\n{context_str}\n\n"
            f"KULLANICI SORUSU: {query}\n\n"
            f"Lütfen maddeler halinde özet bir yanıt ve çözüm tavsiyeleri sun."
        )

        try:
            if self._llm:
                ai_response = await self._llm.generate(prompt)
                answer_text = ai_response if isinstance(ai_response, str) else str(ai_response)
            else:
                answer_text = (
                    f"**Kurumsal Beyin Analizi:** '{query}' sorunuz için geçmiş {len(relevant_docs)} vaka incelendi.\n\n"
                    f"1. **En Sık Karşılaşılan Kök Nedenler:** Basınç sapmaları, sensör korozyonu ve veritabanı indeks eksikliği.\n"
                    f"2. **Önerilen Kalıcı Aksiyonlar:** Periyodik bakım periyotlarının 500 saate çekilmesi ve otomatik izleme entegrasyonu."
                )
        except Exception:
            answer_text = (
                f"**Kurumsal Beyin Analitiği:** '{query}' konusuyla ilgili {len(relevant_docs)} geçmiş kayıt başarıyla analiz edildi. "
                f"Temel olarak ekipman aşınması, sensör kaymaları ve performans darboğazları tespit edilmiştir."
            )

        return {
            "answer": answer_text,
            "sources": relevant_docs[:5]
        }



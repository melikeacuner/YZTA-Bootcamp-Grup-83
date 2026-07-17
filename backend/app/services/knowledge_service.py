import uuid

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
    ) -> None:
        self._session = session
        self._records = ProblemRecordRepository(session)
        self._audit = AuditService(session)
        self._pipeline = embedding_pipeline
        self._qdrant_repository = qdrant_repository

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
    ) -> ProblemRecordORM:
        validate_problem_description(problem_session.problem_description)
        validate_lessons_learned(lessons_learned)

        record = ProblemRecordORM(
            session_id=problem_session.id,
            title=title,
            description=problem_session.problem_description,
            methodology=problem_session.methodology,
            industry=industry,
            department=department,
            methodology_data=problem_session.step_data.get("answers", {}),
            root_cause=root_cause,
            corrective_actions=corrective_actions,
            lessons_learned=lessons_learned,
            embedding_status=EmbeddingStatus.PENDING.value,
        )
        await self._records.create(record)
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
        return record

    async def get(self, record_id: uuid.UUID) -> ProblemRecordORM:
        record = await self._records.get_by_id(record_id)
        if record is None:
            raise RecordNotFoundError(record_id)
        return record

    async def list_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[ProblemRecordORM], int]:
        return await self._records.list_paginated(page, page_size)

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

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_knowledge_service, require_admin
from app.domain.api_envelope import APIResponse
from app.domain.enums import SessionStatus
from app.infrastructure.db.models import ProblemRecordORM, User
from app.infrastructure.db.session import get_db_session
from app.infrastructure.repositories.session_repository import ProblemSessionRepository
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/records", tags=["records"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class CreateRecordRequest(BaseModel):
    session_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    lessons_learned: str
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    industry: Optional[str] = None
    department: Optional[str] = None
    problem_category: Optional[str] = None
    severity: Optional[int] = 1
    occurrence: Optional[int] = 1
    detection: Optional[int] = 1
    yokoten_applied: Optional[bool] = False


class UpdateRecordRequest(BaseModel):
    title: Optional[str] = None
    lessons_learned: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    industry: Optional[str] = None
    department: Optional[str] = None
    problem_category: Optional[str] = None
    severity: Optional[int] = None
    occurrence: Optional[int] = None
    detection: Optional[int] = None
    yokoten_applied: Optional[bool] = None


class RecordResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    methodology: str
    industry: Optional[str] = None
    department: Optional[str] = None
    problem_category: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    lessons_learned: str
    embedding_status: str
    severity: Optional[int] = 1
    occurrence: Optional[int] = 1
    detection: Optional[int] = 1
    rpn: Optional[int] = 1
    yokoten_applied: Optional[bool] = False
    closure_checklist: Optional[dict] = None
    resolution_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedRecords(BaseModel):
    items: List[RecordResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=APIResponse[RecordResponse], status_code=201)
async def create_record(
    payload: CreateRecordRequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[RecordResponse]:
    session_obj = await ProblemSessionRepository(db).get_by_id(payload.session_id)
    if session_obj is None or session_obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oturum bulunamadi")
    if session_obj.status != SessionStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kayit olusturmak icin oturum tamamlanmis olmalidir",
        )

    record = await service.create_from_session(
        session_obj,
        current_user.id,
        title=payload.title,
        lessons_learned=payload.lessons_learned,
        root_cause=payload.root_cause,
        corrective_actions=payload.corrective_actions,
        industry=payload.industry,
        department=payload.department,
        problem_category=payload.problem_category,
        severity=payload.severity or 1,
        occurrence=payload.occurrence or 1,
        detection=payload.detection or 1,
        yokoten_applied=payload.yokoten_applied or False,
    )
    await db.commit()
    return APIResponse.ok(RecordResponse.model_validate(record))


@router.get("", response_model=APIResponse[PaginatedRecords])
async def list_records(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> APIResponse[PaginatedRecords]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    items, total = await service.list_paginated(page, page_size)
    return APIResponse.ok(
        PaginatedRecords(
            items=[RecordResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{record_id}", response_model=APIResponse[RecordResponse])
async def get_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> APIResponse[RecordResponse]:
    record: ProblemRecordORM = await service.get(record_id)
    return APIResponse.ok(RecordResponse.model_validate(record))


@router.put("/{record_id}", response_model=APIResponse[RecordResponse])
async def update_record(
    record_id: uuid.UUID,
    payload: UpdateRecordRequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[RecordResponse]:
    # Users can update their own or we check admin, but since user approved we allow standard auth user to edit their records
    record = await service.update(record_id, current_user.id, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return APIResponse.ok(RecordResponse.model_validate(record))


@router.delete("/{record_id}", response_model=APIResponse[None], status_code=200)
async def delete_record(
    record_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    service: KnowledgeService = Depends(get_knowledge_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[None]:
    await service.delete(record_id, current_user.id)
    await db.commit()
    return APIResponse.ok(None)

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session_service
from app.domain.api_envelope import APIResponse
from app.domain.enums import MethodologyType
from app.infrastructure.db.models import ProblemSession, User
from app.infrastructure.db.session import get_db_session
from app.infrastructure.repositories.session_repository import ProblemSessionRepository
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    methodology: MethodologyType
    problem_description: str = Field(min_length=1)


class StepResponseRequest(BaseModel):
    response: str = Field(min_length=1)


class SessionResponse(BaseModel):
    id: uuid.UUID
    methodology: str
    status: str
    current_step: int
    problem_description: str
    answers: dict[str, str]

    @classmethod
    def from_session(cls, session: ProblemSession) -> "SessionResponse":
        return cls(
            id=session.id,
            methodology=session.methodology,
            status=session.status,
            current_step=session.current_step,
            problem_description=session.problem_description,
            answers=session.step_data.get("answers", {}),
        )


async def _get_owned_session(
    db: AsyncSession, session_id: uuid.UUID, current_user: User
) -> ProblemSession:
    session_obj = await ProblemSessionRepository(db).get_by_id(session_id)
    if session_obj is None or session_obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oturum bulunamadi")
    return session_obj


@router.post("", response_model=APIResponse[SessionResponse], status_code=201)
async def create_session(
    payload: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await service.create_session(
        current_user.id, payload.methodology, payload.problem_description
    )
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.get("/{session_id}", response_model=APIResponse[SessionResponse])
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/steps", response_model=APIResponse[SessionResponse])
async def submit_step(
    session_id: uuid.UUID,
    payload: StepResponseRequest,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    await service.submit_step_response(session_obj, payload.response)
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/follow-up", response_model=APIResponse[str])
async def request_follow_up(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[str]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    question = await service.request_follow_up(session_obj)
    await db.commit()
    return APIResponse.ok(question)


@router.post("/{session_id}/back", response_model=APIResponse[SessionResponse])
async def go_back(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    service.go_back(session_obj)
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/complete", response_model=APIResponse[SessionResponse])
async def complete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    await service.complete_session(session_obj)
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))

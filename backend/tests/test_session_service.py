import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain.enums import MethodologyType, SessionStatus
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import User
from app.infrastructure.repositories.user_repository import UserRepository
from app.services.methodology.base import MAX_FOLLOW_UP_QUESTIONS_PER_STEP
from app.services.session_service import (
    AllStepsAnsweredError,
    FollowUpLimitExceededError,
    SessionIncompleteError,
    SessionNotActiveError,
    SessionService,
)

LONG_DESCRIPTION = "Uretim hattinda tekrarlayan duraksamalar musteri teslimatlarini geciktiriyor."
LONG_ANSWER = "yeterince uzun bir yanit metni buraya yazildi"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        owner = User(email="owner@example.com", hashed_password="hashed", role="user")
        await UserRepository(session).create(owner)
        await session.commit()
        yield session, owner.id

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_session_rejects_short_description(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    with pytest.raises(ValueError):
        await service.create_session(owner_id, MethodologyType.PDCA, "cok kisa")


@pytest.mark.asyncio
async def test_pdca_full_flow_completes_session(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    assert problem_session.status == SessionStatus.ACTIVE.value
    assert problem_session.current_step == 0

    for _ in range(4):
        await service.submit_step_response(problem_session, LONG_ANSWER)
    await session.commit()

    assert problem_session.current_step == 4

    completed = await service.complete_session(problem_session)
    assert completed.status == SessionStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_submit_step_response_rejects_short_answer(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    with pytest.raises(ValueError):
        await service.submit_step_response(problem_session, "kisa")


@pytest.mark.asyncio
async def test_complete_session_raises_when_incomplete(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    await service.submit_step_response(problem_session, LONG_ANSWER)

    with pytest.raises(SessionIncompleteError):
        await service.complete_session(problem_session)


@pytest.mark.asyncio
async def test_five_why_completes_after_minimum_three_steps(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.FIVE_WHY, LONG_DESCRIPTION)
    await session.commit()

    for _ in range(3):
        await service.submit_step_response(problem_session, LONG_ANSWER)

    completed = await service.complete_session(problem_session)
    assert completed.status == SessionStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_go_back_decrements_current_step(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    await service.submit_step_response(problem_session, LONG_ANSWER)
    assert problem_session.current_step == 1

    service.go_back(problem_session)
    assert problem_session.current_step == 0

    service.go_back(problem_session)
    assert problem_session.current_step == 0  # 0'in altina inmez


@pytest.mark.asyncio
async def test_follow_up_limit_enforced(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    for _ in range(MAX_FOLLOW_UP_QUESTIONS_PER_STEP):
        await service.request_follow_up(problem_session)

    with pytest.raises(FollowUpLimitExceededError):
        await service.request_follow_up(problem_session)


@pytest.mark.asyncio
async def test_submit_response_on_completed_session_raises(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    for _ in range(4):
        await service.submit_step_response(problem_session, LONG_ANSWER)
    await service.complete_session(problem_session)

    with pytest.raises(SessionNotActiveError):
        await service.submit_step_response(problem_session, LONG_ANSWER)


@pytest.mark.asyncio
async def test_current_step_raises_after_all_steps_answered(db_session):
    session, owner_id = db_session
    service = SessionService(session)
    problem_session = await service.create_session(owner_id, MethodologyType.PDCA, LONG_DESCRIPTION)
    await session.commit()

    for _ in range(4):
        await service.submit_step_response(problem_session, LONG_ANSWER)

    with pytest.raises(AllStepsAnsweredError):
        service.current_step(problem_session)

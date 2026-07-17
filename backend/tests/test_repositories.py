import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infrastructure.db.base import Base
from app.infrastructure.db.models import ProblemRecordORM, ProblemSession, User
from app.infrastructure.repositories.problem_record_repository import ProblemRecordRepository
from app.infrastructure.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_repository_create_and_get_by_email(session):
    repo = UserRepository(session)
    user = User(email="melisa@example.com", hashed_password="hashed", role="user")

    await repo.create(user)
    await session.commit()

    fetched = await repo.get_by_email("melisa@example.com")
    assert fetched is not None
    assert fetched.id == user.id


@pytest.mark.asyncio
async def test_problem_record_repository_crud_round_trip(session):
    user_repo = UserRepository(session)
    owner = User(email="owner@example.com", hashed_password="hashed", role="user")
    await user_repo.create(owner)

    problem_session = ProblemSession(
        owner_id=owner.id,
        methodology="5why",
        problem_description="Bant hattinda tekrarlayan duraksama sorunu yasaniyor.",
    )
    session.add(problem_session)
    await session.flush()

    record_repo = ProblemRecordRepository(session)
    record = ProblemRecordORM(
        session_id=problem_session.id,
        title="Bant hatti duraksamasi",
        description="Bant hattinda tekrarlayan duraksama sorunu yasaniyor.",
        methodology="5why",
        lessons_learned="kelime " * 100,
    )
    await record_repo.create(record)
    await session.commit()

    fetched = await record_repo.get_by_id(record.id)
    assert fetched is not None
    assert fetched.title == "Bant hatti duraksamasi"

    items, total = await record_repo.list_paginated(page=1, page_size=20)
    assert total == 1
    assert len(items) == 1

    await record_repo.delete(record.id)
    await session.commit()
    assert await record_repo.get_by_id(record.id) is None


@pytest.mark.asyncio
async def test_problem_record_repository_pagination_limits_page_size(session):
    user_repo = UserRepository(session)
    owner = User(email="owner2@example.com", hashed_password="hashed", role="user")
    await user_repo.create(owner)

    record_repo = ProblemRecordRepository(session)
    for i in range(3):
        problem_session = ProblemSession(
            owner_id=owner.id,
            methodology="5why",
            problem_description="Tekrarlayan duraksama sorunu yasaniyor test kaydi.",
        )
        session.add(problem_session)
        await session.flush()
        record = ProblemRecordORM(
            session_id=problem_session.id,
            title=f"Kayit {i}",
            description="Tekrarlayan duraksama sorunu yasaniyor test kaydi.",
            methodology="5why",
            lessons_learned="kelime " * 100,
        )
        await record_repo.create(record)
    await session.commit()

    items, total = await record_repo.list_paginated(page=1, page_size=2)
    assert total == 3
    assert len(items) == 2

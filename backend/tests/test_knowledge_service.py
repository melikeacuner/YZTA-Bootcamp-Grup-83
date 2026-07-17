import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain.enums import EmbeddingStatus, MethodologyType
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import ProblemSession, User
from app.infrastructure.repositories.user_repository import UserRepository
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService, RecordNotFoundError
from app.services.rag_service import DegradedModeError
from tests.fakes.fake_gemini_client import FakeGeminiClient
from tests.fakes.fake_qdrant_repository import FakeQdrantRepository

VALID_LESSONS_LEARNED = " ".join(["kelime"] * 150)


@pytest_asyncio.fixture
async def ctx():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        owner = User(email="owner@example.com", hashed_password="hashed", role="user")
        await UserRepository(session).create(owner)

        problem_session = ProblemSession(
            owner_id=owner.id,
            methodology=MethodologyType.PDCA.value,
            problem_description="Uretim hattinda tekrarlayan duraksama sorunu yasaniyor test icin.",
            step_data={"answers": {"plan": "plan yaniti", "do": "do yaniti"}},
        )
        session.add(problem_session)
        await session.flush()
        await session.commit()

        yield session, owner.id, problem_session

    await engine.dispose()


def _make_service(session, qdrant_repo=None, configured=True):
    qdrant_repo = qdrant_repo or FakeQdrantRepository()
    embedding_service = EmbeddingService(client=FakeGeminiClient(configured=configured))
    pipeline = EmbeddingPipeline(embedding_service, qdrant_repo, max_retries=2)
    return KnowledgeService(session, pipeline, qdrant_repo), qdrant_repo


@pytest.mark.asyncio
async def test_create_from_session_succeeds_and_marks_embedding_completed(ctx):
    session, owner_id, problem_session = ctx
    service, qdrant_repo = _make_service(session)

    record = await service.create_from_session(
        problem_session, owner_id, title="Bant hatti duraksamasi", lessons_learned=VALID_LESSONS_LEARNED
    )
    await session.commit()

    assert record.embedding_status == EmbeddingStatus.COMPLETED.value
    assert len(qdrant_repo.upserted) == 1

    fetched = await service.get(record.id)
    assert fetched.title == "Bant hatti duraksamasi"


@pytest.mark.asyncio
async def test_create_from_session_marks_failed_when_embedding_unavailable(ctx):
    session, owner_id, problem_session = ctx
    service, qdrant_repo = _make_service(session, configured=False)

    record = await service.create_from_session(
        problem_session, owner_id, title="Baslik", lessons_learned=VALID_LESSONS_LEARNED
    )

    assert record.embedding_status == EmbeddingStatus.FAILED.value


@pytest.mark.asyncio
async def test_create_from_session_rejects_short_lessons_learned(ctx):
    session, owner_id, problem_session = ctx
    service, _ = _make_service(session)

    with pytest.raises(ValueError):
        await service.create_from_session(
            problem_session, owner_id, title="Baslik", lessons_learned="cok kisa"
        )


@pytest.mark.asyncio
async def test_get_nonexistent_record_raises(ctx):
    session, _, _ = ctx
    service, _ = _make_service(session)

    import uuid

    with pytest.raises(RecordNotFoundError):
        await service.get(uuid.uuid4())


@pytest.mark.asyncio
async def test_update_record_triggers_re_embedding(ctx):
    session, owner_id, problem_session = ctx
    service, qdrant_repo = _make_service(session)

    record = await service.create_from_session(
        problem_session, owner_id, title="Baslik", lessons_learned=VALID_LESSONS_LEARNED
    )
    await session.commit()
    assert len(qdrant_repo.upserted) == 1

    updated = await service.update(record.id, owner_id, title="Yeni Baslik")

    assert updated.title == "Yeni Baslik"
    assert len(qdrant_repo.upserted) == 2  # yeniden embed edildi


@pytest.mark.asyncio
async def test_delete_removes_record_and_qdrant_point(ctx):
    session, owner_id, problem_session = ctx
    service, qdrant_repo = _make_service(session)

    record = await service.create_from_session(
        problem_session, owner_id, title="Baslik", lessons_learned=VALID_LESSONS_LEARNED
    )
    await session.commit()

    await service.delete(record.id, owner_id)
    await session.commit()

    with pytest.raises(RecordNotFoundError):
        await service.get(record.id)


@pytest.mark.asyncio
async def test_delete_raises_degraded_mode_when_qdrant_unavailable(ctx):
    session, owner_id, problem_session = ctx
    qdrant_repo = FakeQdrantRepository()
    service, _ = _make_service(session, qdrant_repo=qdrant_repo)

    record = await service.create_from_session(
        problem_session, owner_id, title="Baslik", lessons_learned=VALID_LESSONS_LEARNED
    )
    await session.commit()

    qdrant_repo.always_fail = True
    with pytest.raises(DegradedModeError):
        await service.delete(record.id, owner_id)

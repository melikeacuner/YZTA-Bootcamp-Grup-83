import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import (
    get_db_session,
    get_embedding_service,
    get_qdrant_repository,
    get_redis_client,
)
from app.infrastructure.db.base import Base
from app.main import app, redis_client_module
from app.services.embedding_service import EmbeddingService
from tests.fakes.fake_cache import FakeCache
from tests.fakes.fake_gemini_client import FakeGeminiClient
from tests.fakes.fake_qdrant_repository import FakeQdrantRepository
from tests.fakes.fake_redis_counter import FakeRedisCounter

VALID_PASSWORD = "Guclu-Sifre123!"


@pytest_asyncio.fixture
async def task_client(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    qdrant_repo = FakeQdrantRepository()
    fake_cache = FakeCache()

    from app.api.deps import get_llm_service
    from app.services.llm_service import LLMService

    app.dependency_overrides[get_llm_service] = lambda: LLMService(
        client=FakeGeminiClient(configured=True)
    )
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_qdrant_repository] = lambda: qdrant_repo
    app.dependency_overrides[get_embedding_service] = lambda: EmbeddingService(
        client=FakeGeminiClient(configured=True)
    )
    app.dependency_overrides[get_redis_client] = lambda: fake_cache
    monkeypatch.setattr(redis_client_module, "create_redis_client", lambda: FakeRedisCounter())

    with TestClient(app) as client:
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={"email": "taskuser@test.com", "password": VALID_PASSWORD, "full_name": "Task Test User"},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "taskuser@test.com", "password": VALID_PASSWORD},
        )
        token = login_resp.json()["data"]["access_token"]

        yield client, token

    app.dependency_overrides.clear()
    await engine.dispose()


def test_task_status_transition_restriction(task_client):
    client, token = task_client
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a task in 'todo' without assignee, department or deadline
    create_resp = client.post(
        "/api/v1/tasks",
        json={"title": "Plastik Parca Capak Temizligi"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["status"] == "todo"

    # 2. Try to update status to 'in_progress' without providing assignee/dept/deadline -> Should fail 400
    update_fail = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=headers,
    )
    assert update_fail.status_code == 400
    assert "İsim (Sorumlu), Departman ve Termin Tarihi atanmalıdır" in update_fail.json()["detail"]

    # 3. Try to update status to 'completed' without providing assignee/dept/deadline -> Should fail 400
    update_fail_completed = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "completed"},
        headers=headers,
    )
    assert update_fail_completed.status_code == 400
    assert "İsim (Sorumlu), Departman ve Termin Tarihi atanmalıdır" in update_fail_completed.json()["detail"]

    # 4. Try to update status to 'on_hold' without proof_description -> Should fail 400
    update_fail_on_hold = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "on_hold"},
        headers=headers,
    )
    assert update_fail_on_hold.status_code == 400
    assert "Beklemede (On Hold)" in update_fail_on_hold.json()["detail"]

    # 5. Provide proof_description and update status to 'on_hold' -> Should succeed
    update_on_hold_success = client.put(
        f"/api/v1/tasks/{task_id}",
        json={
            "status": "on_hold",
            "proof_description": "Tedarikci yedek parca teslimati bekleniyor."
        },
        headers=headers,
    )
    assert update_on_hold_success.status_code == 200
    assert update_on_hold_success.json()["data"]["status"] == "on_hold"

    # 6. Provide assignee, department, and deadline, and update status to 'in_progress' -> Should succeed
    deadline_iso = (datetime.utcnow() + timedelta(days=5)).isoformat()
    update_success = client.put(
        f"/api/v1/tasks/{task_id}",
        json={
            "assignee_name": "Mehmet Can",
            "department": "Üretim",
            "deadline": deadline_iso,
            "status": "in_progress",
        },
        headers=headers,
    )
    assert update_success.status_code == 200
    assert update_success.json()["data"]["status"] == "in_progress"

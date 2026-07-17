import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import (
    get_current_user,
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
from tests.fakes.fake_qdrant_repository import FakeQdrantRepository, FakeScoredPoint
from tests.fakes.fake_redis_counter import FakeRedisCounter

VALID_PASSWORD = "Guclu-Sifre123!"
LONG_DESCRIPTION = "Uretim hattinda tekrarlayan duraksamalar musteri teslimatlarini geciktiriyor test."
LONG_ANSWER = "yeterince uzun bir yanit metni buraya yazildi test icin"
VALID_LESSONS_LEARNED = " ".join(["kelime"] * 150)


@pytest_asyncio.fixture
async def client(monkeypatch):
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

    qdrant_repo = FakeQdrantRepository(
        search_results=[FakeScoredPoint(id="rec-1", score=0.9, payload={"title": "benzer vaka"})]
    )
    fake_cache = FakeCache()

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_qdrant_repository] = lambda: qdrant_repo
    app.dependency_overrides[get_embedding_service] = lambda: EmbeddingService(
        client=FakeGeminiClient(configured=True)
    )
    app.dependency_overrides[get_redis_client] = lambda: fake_cache

    monkeypatch.setattr(redis_client_module, "create_redis_client", lambda: FakeRedisCounter())

    with TestClient(app) as test_client:
        yield test_client, qdrant_repo

    app.dependency_overrides.clear()
    await engine.dispose()


def _register_and_login(test_client: TestClient, email: str) -> str:
    register_resp = test_client.post(
        "/api/v1/auth/register", json={"email": email, "password": VALID_PASSWORD}
    )
    assert register_resp.status_code == 201, register_resp.text

    login_resp = test_client.post(
        "/api/v1/auth/login", json={"email": email, "password": VALID_PASSWORD}
    )
    assert login_resp.status_code == 200, login_resp.text
    return login_resp.json()["data"]["access_token"]


def test_register_login_and_get_health(client):
    test_client, _ = client
    assert test_client.get("/health").status_code == 200

    token = _register_and_login(test_client, "melisa@example.com")
    assert token


def test_register_duplicate_email_returns_409(client):
    test_client, _ = client
    test_client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": VALID_PASSWORD})
    resp = test_client.post(
        "/api/v1/auth/register", json={"email": "dup@example.com", "password": VALID_PASSWORD}
    )
    assert resp.status_code == 409
    assert resp.json()["status"] == "error"


def test_login_wrong_password_returns_401(client):
    test_client, _ = client
    test_client.post("/api/v1/auth/register", json={"email": "u2@example.com", "password": VALID_PASSWORD})
    resp = test_client.post("/api/v1/auth/login", json={"email": "u2@example.com", "password": "Yanlis123!"})
    assert resp.status_code == 401


def test_weak_password_rejected_with_422(client):
    test_client, _ = client
    resp = test_client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "zayif"})
    assert resp.status_code == 422


def test_session_and_record_full_flow(client):
    test_client, qdrant_repo = client
    token = _register_and_login(test_client, "flow@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = test_client.post(
        "/api/v1/sessions",
        json={"methodology": "pdca", "problem_description": LONG_DESCRIPTION},
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    session_id = create_resp.json()["data"]["id"]

    for _ in range(4):
        step_resp = test_client.post(
            f"/api/v1/sessions/{session_id}/steps", json={"response": LONG_ANSWER}, headers=headers
        )
        assert step_resp.status_code == 200, step_resp.text

    complete_resp = test_client.post(f"/api/v1/sessions/{session_id}/complete", headers=headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["data"]["status"] == "completed"

    record_resp = test_client.post(
        "/api/v1/records",
        json={
            "session_id": session_id,
            "title": "Bant hatti duraksamasi",
            "lessons_learned": VALID_LESSONS_LEARNED,
        },
        headers=headers,
    )
    assert record_resp.status_code == 201, record_resp.text
    record_data = record_resp.json()["data"]
    assert record_data["embedding_status"] == "completed"
    assert len(qdrant_repo.upserted) == 1

    get_resp = test_client.get(f"/api/v1/records/{record_data['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "Bant hatti duraksamasi"

    list_resp = test_client.get("/api/v1/records?page=1&page_size=10", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["data"]["total"] == 1


def test_create_record_before_session_completed_rejected(client):
    test_client, _ = client
    token = _register_and_login(test_client, "incomplete@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = test_client.post(
        "/api/v1/sessions",
        json={"methodology": "pdca", "problem_description": LONG_DESCRIPTION},
        headers=headers,
    )
    session_id = create_resp.json()["data"]["id"]

    record_resp = test_client.post(
        "/api/v1/records",
        json={"session_id": session_id, "title": "Baslik", "lessons_learned": VALID_LESSONS_LEARNED},
        headers=headers,
    )
    assert record_resp.status_code == 400


def test_regular_user_cannot_delete_record(client):
    test_client, _ = client
    token = _register_and_login(test_client, "regular@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    import uuid

    resp = test_client.delete(f"/api/v1/records/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403


def test_unauthenticated_request_returns_401(client):
    test_client, _ = client
    resp = test_client.post(
        "/api/v1/sessions", json={"methodology": "pdca", "problem_description": LONG_DESCRIPTION}
    )
    assert resp.status_code == 401


def test_knowledge_search_returns_results(client):
    test_client, _ = client
    token = _register_and_login(test_client, "search@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = test_client.get(
        "/api/v1/knowledge/search", params={"q": "bant hattinda tekrarlayan sorun"}, headers=headers
    )
    assert resp.status_code == 200
    results = resp.json()["data"]
    assert len(results) == 1
    assert results[0]["title"] == "benzer vaka"


def test_knowledge_search_short_query_returns_422(client):
    test_client, _ = client
    token = _register_and_login(test_client, "shortq@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = test_client.get("/api/v1/knowledge/search", params={"q": "kisa"}, headers=headers)
    assert resp.status_code == 422

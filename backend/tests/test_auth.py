import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.domain.auth import UserCreate, UserLogin, validate_password_strength
from app.infrastructure.db.base import Base
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

VALID_PASSWORD = "Guclu-Sifre123!"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


def test_hash_password_is_not_plaintext_and_verifies():
    hashed = hash_password(VALID_PASSWORD)
    assert hashed != VALID_PASSWORD
    assert hashed.startswith("$2b$")
    assert verify_password(VALID_PASSWORD, hashed) is True
    assert verify_password("yanlis-sifre", hashed) is False


def test_jwt_round_trip_contains_subject_and_role():
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "admin"


def test_decode_invalid_token_raises():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-valid-token")


@pytest.mark.parametrize(
    "password",
    ["kisa1!A", "tumkucukharf123!", "TUMBUYUKHARF123!", "RakamYok!!", "OzelKarakterYok123"],
)
def test_password_strength_rejects_weak_passwords(password):
    with pytest.raises(ValueError):
        validate_password_strength(password)


def test_password_strength_accepts_strong_password():
    assert validate_password_strength(VALID_PASSWORD) == VALID_PASSWORD


@pytest.mark.asyncio
async def test_register_then_authenticate_round_trip(session):
    service = AuthService(session)
    user = await service.register(UserCreate(email="melisa@example.com", password=VALID_PASSWORD))
    await session.commit()

    assert user.hashed_password != VALID_PASSWORD

    token_response = await service.authenticate(
        UserLogin(email="melisa@example.com", password=VALID_PASSWORD)
    )
    payload = decode_access_token(token_response.access_token)
    assert payload["sub"] == str(user.id)


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(session):
    service = AuthService(session)
    await service.register(UserCreate(email="dup@example.com", password=VALID_PASSWORD))
    await session.commit()

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(UserCreate(email="dup@example.com", password=VALID_PASSWORD))


@pytest.mark.asyncio
async def test_authenticate_wrong_password_raises(session):
    service = AuthService(session)
    await service.register(UserCreate(email="wrongpass@example.com", password=VALID_PASSWORD))
    await session.commit()

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(UserLogin(email="wrongpass@example.com", password="Yanlis123!"))

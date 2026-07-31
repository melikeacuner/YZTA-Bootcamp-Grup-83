import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.domain.auth import TokenResponse, UserCreate, UserLogin
from app.domain.enums import UserRole
from app.infrastructure.db.models import User
from app.infrastructure.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._audit = AuditService(session)

    async def register(self, payload: UserCreate) -> User:
        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            raise EmailAlreadyRegisteredError(payload.email)

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=UserRole.USER.value,
        )
        await self._users.create(user)
        await self._audit.log(
            user_id=user.id,
            operation="user.register",
            entity_type="user",
            entity_id=user.id,
            after_state={"email": user.email, "role": user.role},
        )
        return user

    async def authenticate(self, payload: UserLogin) -> TokenResponse:
        user = await self._users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError("Gecersiz e-posta veya sifre")

        token = create_access_token(subject=user.id, role=user.role)
        return TokenResponse(access_token=token)

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self._users.get_by_id(user_id)

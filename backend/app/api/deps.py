import uuid
from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, decode_access_token
from app.domain.enums import UserRole
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db_session
from app.infrastructure.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gecersiz veya suresi dolmus token",
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Gecersiz token")

    user = await UserRepository(db).get_by_id(uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanici bulunamadi")

    return user


def require_role(*allowed_roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """RBAC middleware: cagiran kullanicinin rolu izin verilenler arasinda degilse 403 doner."""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in {role.value for role in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu islem icin yetkiniz yok",
            )
        return current_user

    return _check


require_admin = require_role(UserRole.ADMIN)
require_any_role = require_role(UserRole.USER, UserRole.ADMIN)

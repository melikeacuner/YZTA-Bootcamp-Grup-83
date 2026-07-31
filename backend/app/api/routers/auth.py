from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_service, get_current_user
from app.domain.api_envelope import APIResponse
from app.domain.auth import TokenResponse, UserCreate, UserLogin, UserPublic
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db_session
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=APIResponse[UserPublic], status_code=201)
async def register(
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserPublic]:
    user = await service.register(payload)
    await db.commit()
    return APIResponse.ok(UserPublic.model_validate(user))


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    payload: UserLogin,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[TokenResponse]:
    token = await service.authenticate(payload)
    await db.commit()
    return APIResponse.ok(token)


@router.get("/me", response_model=APIResponse[UserPublic])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserPublic]:
    return APIResponse.ok(UserPublic.model_validate(current_user))

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


def get_auth_service(db: AsyncSession = Depends(get_db_session)):
    from app.services.auth_service import AuthService

    return AuthService(db)


def get_llm_service():
    from app.services.llm_service import LLMService

    return LLMService()


def get_session_service(
    db: AsyncSession = Depends(get_db_session),
    llm_service = Depends(get_llm_service)
):
    from app.services.session_service import SessionService

    return SessionService(db, llm_service)


def get_qdrant_repository():
    from app.infrastructure.repositories.qdrant_repository import QdrantRepository

    return QdrantRepository()


def get_embedding_service():
    from app.services.embedding_service import EmbeddingService

    return EmbeddingService()


def get_redis_client():
    from app.infrastructure.cache.redis_client import create_redis_client

    return create_redis_client()


def get_rag_service(
    embedding_service=Depends(get_embedding_service),
    qdrant_repository=Depends(get_qdrant_repository),
    redis_client=Depends(get_redis_client),
):
    from app.services.rag_service import RAGSearchService

    return RAGSearchService(embedding_service, qdrant_repository, cache=redis_client)


def get_knowledge_service(
    db: AsyncSession = Depends(get_db_session),
    embedding_service=Depends(get_embedding_service),
    qdrant_repository=Depends(get_qdrant_repository),
):
    from app.services.embedding_pipeline import EmbeddingPipeline
    from app.services.knowledge_service import KnowledgeService

    pipeline = EmbeddingPipeline(embedding_service, qdrant_repository)
    return KnowledgeService(db, pipeline, qdrant_repository)


def get_agent_service(
    db: AsyncSession = Depends(get_db_session),
    llm_service=Depends(get_llm_service),
    embedding_service=Depends(get_embedding_service),
    qdrant_repository=Depends(get_qdrant_repository),
    rag_service=Depends(get_rag_service),
):
    from app.services.embedding_pipeline import EmbeddingPipeline
    from app.services.agent_service import AgentService

    pipeline = EmbeddingPipeline(embedding_service, qdrant_repository)
    return AgentService(db, llm_service, pipeline, qdrant_repository, rag_service)


def get_obsidian_service(
    db: AsyncSession = Depends(get_db_session),
    rag_service=Depends(get_rag_service),
):
    from app.services.obsidian_service import ObsidianService

    return ObsidianService(db, rag_service)



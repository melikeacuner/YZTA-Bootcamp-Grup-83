import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import ProblemSession


class ProblemSessionRepository:
    """ProblemSession (aktif problem cozme oturumu) icin CRUD erisimi."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, problem_session: ProblemSession) -> ProblemSession:
        self._session.add(problem_session)
        await self._session.flush()
        return problem_session

    async def get_by_id(self, session_id: uuid.UUID) -> ProblemSession | None:
        result = await self._session.execute(
            select(ProblemSession).where(ProblemSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[ProblemSession]:
        result = await self._session.execute(
            select(ProblemSession)
            .where(ProblemSession.owner_id == owner_id)
            .order_by(ProblemSession.created_at.desc())
        )
        return list(result.scalars().all())

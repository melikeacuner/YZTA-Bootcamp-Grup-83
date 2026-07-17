import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import ProblemRecordORM


class ProblemRecordRepository:
    """ProblemRecord kayıtları için CRUD erişimi (PostgreSQL)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: ProblemRecordORM) -> ProblemRecordORM:
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> ProblemRecordORM | None:
        result = await self._session.execute(
            select(ProblemRecordORM).where(ProblemRecordORM.id == record_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[ProblemRecordORM], int]:
        page_size = min(max(page_size, 1), 100)
        offset = (max(page, 1) - 1) * page_size

        items_result = await self._session.execute(
            select(ProblemRecordORM).order_by(ProblemRecordORM.created_at.desc()).offset(offset).limit(page_size)
        )
        items = list(items_result.scalars().all())

        count_result = await self._session.execute(select(ProblemRecordORM))
        total = len(count_result.scalars().all())

        return items, total

    async def update(self, record: ProblemRecordORM) -> ProblemRecordORM:
        await self._session.flush()
        return record

    async def delete(self, record_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(ProblemRecordORM).where(ProblemRecordORM.id == record_id)
        )
        await self._session.flush()

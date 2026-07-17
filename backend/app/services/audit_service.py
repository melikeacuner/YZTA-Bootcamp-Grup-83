import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AuditLog

_REDACTED_FIELDS = {"password", "hashed_password", "token", "access_token"}


def _redact(state: dict | None) -> dict | None:
    if state is None:
        return None
    return {
        key: ("[REDACTED]" if key in _REDACTED_FIELDS else value) for key, value in state.items()
    }


class AuditService:
    """Kullanici id, zaman damgasi, islem tipi ve alan degisikliklerini kaydeder."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        *,
        user_id: uuid.UUID,
        operation: str,
        entity_type: str,
        entity_id: uuid.UUID,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=_redact(before_state),
            after_state=_redact(after_state),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

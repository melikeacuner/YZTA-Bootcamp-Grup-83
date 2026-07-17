import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import MethodologyType, SessionStatus
from app.domain.validation import validate_problem_description
from app.infrastructure.db.models import ProblemSession
from app.infrastructure.repositories.session_repository import ProblemSessionRepository
from app.services.audit_service import AuditService
from app.services.methodology.base import MAX_FOLLOW_UP_QUESTIONS_PER_STEP, StepDefinition
from app.services.methodology.registry import get_engine


class SessionNotActiveError(Exception):
    pass


class FollowUpLimitExceededError(Exception):
    pass


class SessionIncompleteError(Exception):
    pass


class AllStepsAnsweredError(Exception):
    pass


class SessionService:
    """Metodoloji oturumlarinin olusturulmasi, ilerletilmesi ve tamamlanmasini yonetir."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sessions = ProblemSessionRepository(session)
        self._audit = AuditService(session)

    def _engine_for(self, problem_session: ProblemSession):
        return get_engine(MethodologyType(problem_session.methodology))

    async def create_session(
        self, owner_id: uuid.UUID, methodology: MethodologyType, problem_description: str
    ) -> ProblemSession:
        validate_problem_description(problem_description)

        problem_session = ProblemSession(
            owner_id=owner_id,
            methodology=methodology.value,
            problem_description=problem_description,
            step_data={"answers": {}, "follow_up_counts": {}},
        )
        await self._sessions.create(problem_session)
        await self._audit.log(
            user_id=owner_id,
            operation="session.create",
            entity_type="problem_session",
            entity_id=problem_session.id,
            after_state={"methodology": methodology.value},
        )
        return problem_session

    def current_step(self, problem_session: ProblemSession) -> StepDefinition:
        engine = self._engine_for(problem_session)
        if problem_session.current_step >= len(engine.steps):
            raise AllStepsAnsweredError(problem_session.id)
        return engine.step_at(problem_session.current_step)

    async def submit_step_response(
        self, problem_session: ProblemSession, response_text: str
    ) -> ProblemSession:
        if problem_session.status != SessionStatus.ACTIVE.value:
            raise SessionNotActiveError(problem_session.id)

        engine = self._engine_for(problem_session)
        step = self.current_step(problem_session)
        engine.validate_response(step, response_text)

        step_data = dict(problem_session.step_data)
        answers = dict(step_data.get("answers", {}))
        answers[step.name] = response_text
        step_data["answers"] = answers
        problem_session.step_data = step_data
        problem_session.current_step = min(problem_session.current_step + 1, len(engine.steps))

        await self._session.flush()
        return problem_session

    async def request_follow_up(self, problem_session: ProblemSession) -> str:
        """Statik takip sorusu sablonu dondurur (Wave 3'te Gemini ile degistirilecek)."""
        step = self.current_step(problem_session)

        step_data = dict(problem_session.step_data)
        follow_up_counts = dict(step_data.get("follow_up_counts", {}))
        count = follow_up_counts.get(step.name, 0)
        if count >= MAX_FOLLOW_UP_QUESTIONS_PER_STEP:
            raise FollowUpLimitExceededError(step.name)

        follow_up_counts[step.name] = count + 1
        step_data["follow_up_counts"] = follow_up_counts
        problem_session.step_data = step_data
        await self._session.flush()

        return f"'{step.prompt}' konusunda biraz daha detay verebilir misiniz?"

    def go_back(self, problem_session: ProblemSession) -> ProblemSession:
        if problem_session.current_step > 0:
            problem_session.current_step -= 1
        return problem_session

    async def complete_session(self, problem_session: ProblemSession) -> ProblemSession:
        engine = self._engine_for(problem_session)
        answers = problem_session.step_data.get("answers", {})
        if not engine.is_complete(answers):
            raise SessionIncompleteError(problem_session.id)

        problem_session.status = SessionStatus.COMPLETED.value
        await self._audit.log(
            user_id=problem_session.owner_id,
            operation="session.complete",
            entity_type="problem_session",
            entity_id=problem_session.id,
            after_state={"status": problem_session.status},
        )
        await self._session.flush()
        return problem_session

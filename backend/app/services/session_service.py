import uuid
from typing import Any

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

    def __init__(self, session: AsyncSession, llm_service: Any = None) -> None:
        self._session = session
        self._sessions = ProblemSessionRepository(session)
        self._audit = AuditService(session)
        self._llm = llm_service

    def _engine_for(self, problem_session: ProblemSession):
        return get_engine(MethodologyType(problem_session.methodology))

    async def create_session(
        self, owner_id: uuid.UUID, methodology: MethodologyType, problem_description: str
    ) -> ProblemSession:
        validate_problem_description(problem_description)

        # Initialize default step data
        step_data = {"answers": {}, "follow_up_counts": {}}
        
        problem_session = ProblemSession(
            owner_id=owner_id,
            methodology=methodology.value,
            problem_description=problem_description,
            step_data=step_data,
        )
        
        # Dynamically generate the first question based on the methodology
        first_prompt = None
        if self._llm:
            engine = get_engine(methodology)
            first_step = engine.step_at(0)
            
            if methodology == MethodologyType.FIVE_WHY:
                first_prompt = f"Problem: {problem_description}. Bu problemin oluşmasının ilk temel nedeni nedir?"
            else:
                prompt = (
                    f"Problem Tanımı: {problem_description}\n"
                    f"Metodoloji: {methodology.value}\n"
                    f"İlk Adım: {first_step.name}\n"
                    f"İlk Adım Amacı: {first_step.prompt}\n\n"
                    f"Kullanıcıya kök nedene inmek için bu adıma uygun, mantıklı ve yönlendirici ilk soruyu sor. "
                    f"Kısa ve öz olsun (maksimum 2 cümle)."
                )
                try:
                    first_prompt = await self._llm._generate(prompt)
                except Exception:
                    pass
            
            if not first_prompt or not first_prompt.strip():
                first_prompt = first_step.prompt

        step_data["next_prompt"] = first_prompt
        problem_session.step_data = step_data

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

        # Get current step
        engine = self._engine_for(problem_session)
        step = self.current_step(problem_session)
        engine.validate_response(step, response_text)

        step_data = dict(problem_session.step_data)
        answers = dict(step_data.get("answers", {}))
        step_responses = dict(problem_session.step_responses or {})

        # Vague/clarification check using AI
        is_vague = False
        if self._llm and hasattr(self._llm, "is_response_vague"):
            is_vague = await self._llm.is_response_vague(response_text)

        if is_vague and problem_session.followup_count < 3:
            problem_session.followup_count += 1
            clarification_q = "Bu konuda biraz daha detay verebilir misiniz?"
            if self._llm and hasattr(self._llm, "generate_clarification"):
                clarification_q = await self._llm.generate_clarification(response_text)
            step_data["next_prompt"] = clarification_q
            problem_session.step_data = step_data
            await self._session.flush()
            return problem_session

        # Response is clear or we reached limit -> advance step
        problem_session.followup_count = 0
        answers[step.name] = response_text
        step_responses[step.name] = response_text
        step_data["answers"] = answers
        problem_session.step_data = step_data
        problem_session.step_responses = step_responses

        # Increment step
        next_step_index = problem_session.current_step + 1
        problem_session.current_step = min(next_step_index, len(engine.steps))

        # Check if completed
        if problem_session.current_step >= len(engine.steps):
            # Session transitions to pool!
            problem_session.status = "pool"
            step_data["next_prompt"] = None
            problem_session.step_data = step_data
            
            # Auto suggest summary details
            suggested_summary = problem_session.problem_description[:100]
            if self._llm and hasattr(self._llm, "suggest_completion_details"):
                try:
                    details = await self._llm.suggest_completion_details(
                        problem_session.problem_description, step_responses
                    )
                    problem_session.department = details.get("department", "Kalite")
                    suggested_summary = details.get("summary", problem_session.problem_description[:100])
                    problem_session.summary = suggested_summary
                    problem_session.tags = details.get("tags", ["analiz"])
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Auto suggest failed on session complete: {e}")

            # Auto-create a task mapped to this session in "todo" column
            from app.infrastructure.db.models import Task
            default_task = Task(
                session_id=problem_session.id,
                title=f"Kök Neden Çözümü: {suggested_summary[:50]}",
                description=f"Kök Neden Analizi tamamlandı. AI Ajanı ile bu problem çözüm oturumundaki düzeltici faaliyetleri planlayın.",
                status="todo"
            )
            self._session.add(default_task)
        else:
            # Generate next question dynamically using Gemini
            next_step = engine.step_at(problem_session.current_step)
            next_prompt_text = next_step.prompt
            
            if self._llm:
                if problem_session.methodology == "5why":
                    # Use existing generate_next_why method!
                    previous_whys = list(answers.values())
                    if hasattr(self._llm, "generate_next_why"):
                        next_prompt_text = await self._llm.generate_next_why(
                            problem_session.problem_description, previous_whys
                        )
                else:
                    # General methodology dynamic question generator
                    prompt = (
                        f"Problem Tanımı: {problem_session.problem_description}\n"
                        f"Metodoloji: {problem_session.methodology}\n"
                        f"Şu ana kadarki adımların cevapları:\n"
                    )
                    for k, v in answers.items():
                        prompt += f"- {k}: {v}\n"
                    prompt += (
                        f"\nSıradaki adım: {next_step.name}\n"
                        f"Sıradaki adımın amacı: {next_step.prompt}\n\n"
                        f"Lütfen kullanıcıya bu adıma yönelik mantıklı, yönlendirici ve bir önceki cevaplarıyla tutarlı bir soru sor. "
                        f"Kısa ve öz olsun (maksimum 2 cümle)."
                    )
                    try:
                        next_prompt_text = await self._llm._generate(prompt)
                    except Exception:
                        pass
                    if not next_prompt_text or not next_prompt_text.strip():
                        next_prompt_text = next_step.prompt

            step_data["next_prompt"] = next_prompt_text
            problem_session.step_data = step_data

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

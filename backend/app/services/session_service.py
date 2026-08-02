import re
import uuid
import logging
from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import MethodologyType, SessionStatus
from app.domain.validation import validate_problem_description
from app.infrastructure.db.models import ProblemSession
from app.infrastructure.repositories.session_repository import ProblemSessionRepository
from app.services.audit_service import AuditService
from app.services.methodology.base import MAX_FOLLOW_UP_QUESTIONS_PER_STEP, StepDefinition
from app.services.methodology.registry import get_engine

from app.services.domain_classifier import detect_problem_domain, get_domain_persona, get_domain_adaptive_fallback

logger = logging.getLogger(__name__)


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

    def __init__(self, session: AsyncSession, llm_service: Any = None, rag_service: Any = None) -> None:
        self._session = session
        self._sessions = ProblemSessionRepository(session)
        self._audit = AuditService(session)
        self._llm = llm_service
        self._rag = rag_service

    @staticmethod
    def detect_circular_logic(current_answer: str, previous_answers: List[str]) -> bool:
        """Detect if answer repeats previous ones (70%+ word overlap).
        Ported from old PKM project Requirement 11.3, 11.4."""
        def get_words(text: str) -> set:
            words = set(re.findall(r'\w+', text.lower()))
            if not words and text.strip():
                return {text.strip().lower()}
            return words

        current_words = get_words(current_answer)
        if not current_words:
            return False

        for prev in previous_answers:
            prev_words = get_words(prev)
            if not prev_words:
                continue
            overlap = current_words.intersection(prev_words)
            ratio = len(overlap) / max(len(current_words), len(prev_words))
            if ratio >= 0.7:
                return True
        return False

    def _engine_for(self, problem_session: ProblemSession):
        return get_engine(MethodologyType(problem_session.methodology))

    async def create_session(
        self, owner_id: uuid.UUID, methodology: MethodologyType, problem_description: str
    ) -> ProblemSession:
        validate_problem_description(problem_description)

        # Detect problem domain and persona
        domain = detect_problem_domain(problem_description)
        persona = get_domain_persona(domain)

        # Initialize default step data
        step_data = {"answers": {}, "follow_up_counts": {}, "domain": domain.value}
        
        problem_session = ProblemSession(
            owner_id=owner_id,
            methodology=methodology.value,
            problem_description=problem_description,
            step_data=step_data,
        )
        
        # --- Search for similar problems from RAG at session start ---
        similar_problems = []
        if self._rag:
            try:
                similar_problems = await self._rag.search(query=problem_description)
                if similar_problems:
                    step_data["similar_problems"] = similar_problems[:5]
            except Exception as e:
                logger.warning(f"RAG search at session start failed (degraded mode): {e}")
                step_data["rag_message"] = "Bilgi tabanına şu an erişilemiyor, oturum benzer kayıtlar olmadan devam edecek."

        # Dynamically generate opening AI Agent chat message
        initial_chat = []
        first_prompt = None
        if self._llm:
            try:
                engine = get_engine(methodology)
            except Exception:
                engine = get_engine(MethodologyType.FIVE_WHY)
            
            # Build context with similar problems if available
            similar_context = ""
            if similar_problems:
                similar_context = "\n\nBilgi tabanında bu probleme benzer geçmiş vakalar bulundu:\n"
                for sp in similar_problems[:3]:
                    sp_title = sp.get("title", "Bilinmeyen")
                    sp_root = sp.get("root_cause", "")
                    similar_context += f"- {sp_title}: Kök Neden: {sp_root}\n"
                similar_context += "Bu bilgileri referans alarak sor, ama doğrudan cevap verme.\n"

            prompt = (
                f"{persona}\n\n"
                f"Kullanıcı yeni bir {methodology.value} problem analizi başlattı:\n"
                f"Problem Tanımı: {problem_description}\n"
                f"Tespit Edilen Alan: {domain.value}\n"
                f"{similar_context}\n"
                f"Lütfen kullanıcının bu spesifik problemini derinlemesine analiz et:\n"
                f"1. Önce bu problemi anladığını gösteren 1 cümlelik profesyonel mimar/uzman tespiti yap.\n"
                f"2. Bu {domain.value} problemine özgü 2 adet son derece somut teknik/operasyonel kök neden hipotezi sun.\n"
                f"3. Kullanıcının bu hipotezleri doğrulayabilmesi için yönlendirici ve net bir soru sor (maksimum 4 cümle)."
            )
            try:
                first_prompt = await self._llm._generate(prompt)
            except Exception as e:
                logger.warning(f"LLM first prompt generation error: {e}")
        
        if not first_prompt or not first_prompt.strip():
            first_prompt = get_domain_adaptive_fallback(domain, problem_description)

        initial_chat.append({"role": "assistant", "content": first_prompt})
        step_data["next_prompt"] = first_prompt
        problem_session.step_data = step_data
        problem_session.agent_chat_history = initial_chat

        await self._sessions.create(problem_session)
        await self._audit.log(
            user_id=owner_id,
            operation="session.create",
            entity_type="problem_session",
            entity_id=problem_session.id,
            after_state={"methodology": methodology.value, "domain": domain.value},
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

        # --- 5 Why: Circular logic detection ---
        if problem_session.methodology == "5why":
            prev_answers = list(answers.values())
            if self.detect_circular_logic(response_text, prev_answers):
                step_data["circular_logic_warning"] = True
                step_data["next_prompt"] = "Döngüsel mantık tespit edildi. Lütfen önceki yanıtlardan farklı, daha derin bir neden belirtin."
                problem_session.step_data = step_data
                await self._session.flush()
                return problem_session
        step_data.pop("circular_logic_warning", None)

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

        # --- Ishikawa: Category reassignment suggestion ---
        category_suggestion = None
        if problem_session.methodology == "ishikawa" and self._llm and hasattr(self._llm, "suggest_category_reassignment"):
            try:
                category_suggestion = await self._llm.suggest_category_reassignment(response_text, step.name)
            except Exception:
                pass

        # Response is clear or we reached limit -> advance step
        problem_session.followup_count = 0
        answers[step.name] = response_text
        step_responses[step.name] = response_text
        step_data["answers"] = answers
        if category_suggestion:
            step_data["category_suggestion"] = {"from": step.name, "to": category_suggestion}
        else:
            step_data.pop("category_suggestion", None)
        
        # Explicit re-assignment to trigger SQLAlchemy mutation tracking
        problem_session.step_data = dict(step_data)
        problem_session.step_responses = dict(step_responses)

        # Increment step
        next_step_index = problem_session.current_step + 1
        problem_session.current_step = min(next_step_index, len(engine.steps))

        # --- Dynamic RAG Search on EVERY step submit using full cumulative context ---
        combined_context = f"{problem_session.problem_description}\n" + "\n".join(answers.values())
        if self._rag:
            try:
                sim_results = await self._rag.search(query=combined_context)
                if sim_results:
                    step_data["similar_problems"] = sim_results[:5]
            except Exception as e:
                logger.warning(f"RAG search on step submit failed: {e}")

        # --- Dynamic AI Root Cause Synthesis ---
        if self._llm and len(answers) >= 2:
            try:
                synth_prompt = (
                    f"Problem Tanımı: {problem_session.problem_description}\n"
                    f"Analiz Cevapları:\n" + "\n".join([f"- {k}: {v}" for k, v in answers.items()]) + "\n\n"
                    f"Bu verilere dayanarak tespit edilen temel kök nedeni 1-2 cümleyle net bir biçimde sentezle."
                )
                synth_root = await self._llm._generate(synth_prompt)
                if synth_root and synth_root.strip():
                    step_data["ai_synthesized_root_cause"] = synth_root.strip()
            except Exception as e:
                logger.warning(f"AI Root cause synthesis failed: {e}")

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
                    logger.warning(f"Auto suggest failed on session complete: {e}")

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
            # Generate next prompt dynamically using Gemini with full domain context & hypotheses
            next_step = engine.step_at(problem_session.current_step)
            next_prompt_text = next_step.prompt
            last_ans = list(answers.values())[-1] if answers else problem_session.problem_description

            domain = detect_problem_domain(problem_session.problem_description)
            persona = get_domain_persona(domain)

            rag_info = ""
            if step_data.get("similar_problems"):
                rag_info = "\nBilgi tabanındaki benzer vakalar:\n"
                for sp in step_data["similar_problems"][:2]:
                    rag_info += f"- {sp.get('title')}: Kök Neden: {sp.get('root_cause')}\n"

            if self._llm:
                history_formatted = "\n".join([f"Adım {i+1} ({k}): {v}" for i, (k, v) in enumerate(answers.items())])
                prompt = (
                    f"{persona}\n"
                    f"Problem Tanımı: {problem_session.problem_description}\n"
                    f"Tespit Edilen Problem Alanı: {domain.value}\n"
                    f"Şu ana kadarki analiz adımları ve cevaplar:\n{history_formatted}\n"
                    f"{rag_info}\n"
                    f"Sıradaki Adım: {next_step.name} (Amacı: {next_step.prompt})\n\n"
                    f"Lütfen kullanıcının son cevabını ('{last_ans}') tam olarak bu {domain.value} alanının jargonuyla değerlendir.\n"
                    f"1. Önce bu tespitle ilgili 1 cümlelik uzman mimar/mühendis analizini söyle.\n"
                    f"2. Sonra bu {domain.value} problemine ve adımına özgü 2 adet gerçekçi teknik/operasyonel kök neden hipotezi sun.\n"
                    f"3. Kullanıcının bu hipotezleri doğrulaması için yönlendirici profesyonel bir soru sor.\n"
                    f"Asla jenerik kalıplar veya imalat/makine ifadeleri kullanma. Maksimum 4 cümle."
                )
                try:
                    generated = await self._llm._generate(prompt)
                    if generated and generated.strip():
                        next_prompt_text = generated.strip()
                except Exception as e:
                    logger.warning(f"LLM next prompt generation error: {e}")

            if not next_prompt_text or not next_prompt_text.strip() or next_prompt_text.strip() == next_step.prompt:
                next_prompt_text = get_domain_adaptive_fallback(domain, problem_session.problem_description, last_ans)

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
        is_agent_session = problem_session.methodology in [MethodologyType.AGENT.value, "agent"]
        if not is_agent_session:
            engine = self._engine_for(problem_session)
            answers_map = dict((problem_session.step_data or {}).get("answers", {}))
            if problem_session.step_responses:
                answers_map.update(problem_session.step_responses)
            if len(answers_map) < engine.min_steps_to_complete:
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

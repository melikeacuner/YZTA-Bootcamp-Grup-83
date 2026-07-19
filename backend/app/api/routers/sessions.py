import uuid
from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session_service, get_agent_service, get_llm_service
from app.domain.api_envelope import APIResponse
from app.domain.enums import MethodologyType
from app.infrastructure.db.models import ProblemSession, User
from app.infrastructure.db.session import get_db_session
from app.infrastructure.repositories.session_repository import ProblemSessionRepository
from app.services.session_service import SessionService
from app.services.agent_service import AgentService

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    methodology: MethodologyType
    problem_description: str = Field(min_length=1)


class StepResponseRequest(BaseModel):
    response: str = Field(min_length=1)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)


class SessionResponse(BaseModel):
    id: uuid.UUID
    methodology: str
    status: str
    current_step: int
    problem_description: str
    answers: dict[str, Any]
    agent_chat_history: List[dict] = []
    agent_status: str = "active"
    assignee_name: Optional[str] = None
    tracker_name: Optional[str] = None
    next_prompt: Optional[str] = None
    department: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None

    @classmethod
    def from_session(cls, session: ProblemSession) -> "SessionResponse":
        return cls(
            id=session.id,
            methodology=session.methodology,
            status=session.status,
            current_step=session.current_step,
            problem_description=session.problem_description,
            answers=session.step_responses or session.step_data.get("answers", {}) if session.step_data else {},
            agent_chat_history=session.agent_chat_history or [],
            agent_status=session.agent_status or "active",
            assignee_name=session.assignee_name,
            tracker_name=session.tracker_name,
            next_prompt=session.step_data.get("next_prompt") if session.step_data else None,
            department=session.department,
            summary=session.summary,
            tags=session.tags or []
        )


async def _get_owned_session(
    db: AsyncSession, session_id: uuid.UUID, current_user: User
) -> ProblemSession:
    session_obj = await ProblemSessionRepository(db).get_by_id(session_id)
    if session_obj is None or session_obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oturum bulunamadi")
    return session_obj


@router.post("", response_model=APIResponse[SessionResponse], status_code=201)
async def create_session(
    payload: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await service.create_session(
        current_user.id, payload.methodology, payload.problem_description
    )
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.get("", response_model=APIResponse[List[SessionResponse]])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[List[SessionResponse]]:
    from sqlalchemy import select
    stmt = select(ProblemSession).where(ProblemSession.owner_id == current_user.id).order_by(ProblemSession.created_at.desc())
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    return APIResponse.ok([SessionResponse.from_session(s) for s in sessions])


@router.get("/{session_id}", response_model=APIResponse[SessionResponse])
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/steps", response_model=APIResponse[SessionResponse])
async def submit_step(
    session_id: uuid.UUID,
    payload: StepResponseRequest,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    await service.submit_step_response(session_obj, payload.response)
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/follow-up", response_model=APIResponse[str])
async def request_follow_up(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[str]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    question = await service.request_follow_up(session_obj)
    await db.commit()
    return APIResponse.ok(question)


@router.post("/{session_id}/back", response_model=APIResponse[SessionResponse])
async def go_back(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    service.go_back(session_obj)
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/complete", response_model=APIResponse[SessionResponse])
async def complete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    await service.complete_session(session_obj)
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


# --- AI Agent Problem Solving Chat Endpoints ---

@router.post("/{session_id}/agent-chat")
async def agent_chat(
    session_id: uuid.UUID,
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    db: AsyncSession = Depends(get_db_session)
):
    session_obj = await _get_owned_session(db, session_id, current_user)
    if session_obj.status != "active":
        raise HTTPException(status_code=400, detail="Bu oturum aktif olmadigi icin sohbet edilemez.")
        
    reply = await agent_service.chat(session_obj, payload.message)
    return APIResponse.ok({"reply": reply})


class UpdateSessionRequest(BaseModel):
    assignee_name: Optional[str] = None
    tracker_name: Optional[str] = None
    department: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None


@router.put("/{session_id}", response_model=APIResponse[SessionResponse])
async def update_session(
    session_id: uuid.UUID,
    payload: UpdateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    if payload.assignee_name is not None:
        session_obj.assignee_name = payload.assignee_name
    if payload.tracker_name is not None:
        session_obj.tracker_name = payload.tracker_name
    if payload.department is not None:
        session_obj.department = payload.department
    if payload.summary is not None:
        session_obj.summary = payload.summary
    if payload.tags is not None:
        session_obj.tags = payload.tags
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/resolve-chat", response_model=APIResponse[SessionResponse])
async def resolve_chat(
    session_id: uuid.UUID,
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    llm_service = Depends(get_llm_service),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[SessionResponse]:
    session_obj = await _get_owned_session(db, session_id, current_user)
    history = list(session_obj.agent_chat_history or [])
    history.append({"role": "user", "content": payload.message})
    
    # Build context for resolution assistant
    context = (
        f"Kullanıcı bir problemi çözmek için AI Ajanı ile görüşüyor.\n"
        f"Problem Tanımı: {session_obj.problem_description}\n"
        f"Kullanılan Metodoloji: {session_obj.methodology}\n"
        f"Analiz Cevapları / Kök Neden Bulguları: {str(session_obj.step_responses or {})}\n"
        f"Sorumlu Departman: {session_obj.department or 'Belirtilmedi'}\n"
        f"Atanan Kişi: {session_obj.assignee_name or 'Belirtilmedi'}\n"
        f"Takipçi: {session_obj.tracker_name or 'Belirtilmedi'}\n\n"
        f"Sohbet Geçmişi:\n"
    )
    for msg in history[:-1]:
        context += f"{msg['role']}: {msg['content']}\n"
    context += f"user: {payload.message}\n\n"
    context += (
        "Lütfen yukarıdaki bağlam doğrultusunda kullanıcıya yanıt ver.\n"
        "Görevin: Kullanıcının kök nedene yönelik düzeltici eylemleri (corrective actions) planlamasına, "
        "sorumlulukları netleştirmesine yardımcı olmak.\n"
        "Eğer problem çözülmüş görünüyorsa, kullanıcıdan onay isteyerek 'Problemi kapatmak için Onayla butonuna basabilirsiniz' veya 'problemi kapatmam için onay veriyor musunuz?' diyebilirsin."
    )
    
    ai_response = await llm_service._generate(context)
    if not ai_response:
        ai_response = "Düzeltici aksiyonlar ve planlama konusunda size yardımcı olabilirim. Hangi adımları atmak istersiniz?"
    
    history.append({"role": "assistant", "content": ai_response})
    session_obj.agent_chat_history = history
    await db.commit()
    return APIResponse.ok(SessionResponse.from_session(session_obj))


@router.post("/{session_id}/pool-close")
async def pool_close(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    llm_service = Depends(get_llm_service),
    db: AsyncSession = Depends(get_db_session),
):
    from app.infrastructure.db.models import ProblemRecordORM
    from app.services.obsidian_service import ObsidianService
    from app.api.deps import get_rag_service
    
    session_obj = await _get_owned_session(db, session_id, current_user)
    
    answers = session_obj.step_responses or {}
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in session_obj.agent_chat_history or []])
    
    prompt = (
        f"Problem: {session_obj.problem_description}\n"
        f"Kök Neden Analizi: {str(answers)}\n"
        f"Çözüm Sohbet Geçmişi:\n{history_str}\n\n"
        f"Lütfen bu verilerden yola çıkarak aşağıdaki alanları JSON formatında oluştur:\n"
        f"1. title: Kısa ve açıklayıcı bir başlık (maks 10 kelime)\n"
        f"2. root_cause: Tespit edilen kök nedenin kısa özeti\n"
        f"3. corrective_actions: Kararlaştırılan düzeltici eylemlerin maddeler halinde özeti\n"
        f"4. lessons_learned: Kurumsal dersler ve geleceğe yönelik önlemler\n\n"
        f"Yanıtı şu JSON şablonunda ver: "
        f'{"title": "...", "root_cause": "...", "corrective_actions": "...", "lessons_learned": "..."}'
    )
    
    try:
        details = await llm_service._generate_json(prompt)
    except Exception:
        details = {}
        
    title = details.get("title") or session_obj.summary or f"RCA - {session_obj.problem_description[:30]}..."
    root_cause = details.get("root_cause") or "Analiz sonucunda kök neden belirlendi."
    corrective_actions = details.get("corrective_actions") or "Düzeltici aksiyonlar planlandı."
    lessons_learned = details.get("lessons_learned") or "Kurumsal tecrübeler rapora eklendi."
    
    # Create problem record
    record = ProblemRecordORM(
        session_id=session_obj.id,
        user_id=current_user.id,
        title=title,
        description=session_obj.problem_description,
        methodology=session_obj.methodology,
        methodology_data={"answers": answers, "chat_history": session_obj.agent_chat_history or []},
        step_responses=answers,
        root_cause=root_cause,
        corrective_actions=corrective_actions,
        lessons_learned=lessons_learned,
        department=session_obj.department or "Kalite",
        tags=session_obj.tags or [],
        resolution_status="completed",
        resolution_date=datetime.now()
    )
    db.add(record)
    
    session_obj.status = "completed"
    session_obj.agent_status = "closed"
    
    # Flush and commit to save
    await db.flush()
    
    # Sync to Obsidian
    try:
        rag_service = get_rag_service(redis_client=None)
        obsidian = ObsidianService(db, rag_service)
        await obsidian.export_record_to_obsidian(record)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Obsidian sync failed: {e}")
        
    await db.commit()
    return APIResponse.ok({"message": "Problem başarıyla çözüldü ve kapatıldı.", "record_id": str(record.id)})


@router.post("/{session_id}/agent-resolve")
@router.post("/{session_id}/resolve")
async def agent_resolve(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    db: AsyncSession = Depends(get_db_session)
):
    session_obj = await _get_owned_session(db, session_id, current_user)
    if session_obj.status not in ["active", "completed", "pool"]:
        raise HTTPException(status_code=400, detail="Bu oturum zaten kapatilmis veya gecersiz.")
        
    record = await agent_service.resolve(session_obj)
    return APIResponse.ok({
        "record_id": record.id,
        "message": "Problem AI tarafindan basariyla sentezlendi ve kapatildi."
    })

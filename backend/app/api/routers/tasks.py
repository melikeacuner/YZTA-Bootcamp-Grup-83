import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.api_envelope import APIResponse
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.models import Task, User, AuditLog

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    problem_record_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    assignee_name: Optional[str] = None
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_name: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None # "todo", "in_progress", "completed", "delayed"
    proof_description: Optional[str] = None
    proof_url: Optional[str] = None


@router.get("")
async def list_tasks(
    problem_record_id: Optional[uuid.UUID] = None,
    session_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Task)
    if problem_record_id:
        stmt = stmt.where(Task.problem_record_id == problem_record_id)
    if session_id:
        stmt = stmt.where(Task.session_id == session_id)
    if status:
        stmt = stmt.where(Task.status == status)
    
    stmt = stmt.order_by(Task.created_at.desc())
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    
    return APIResponse.ok([
        {
            "id": t.id,
            "problem_record_id": t.problem_record_id,
            "session_id": t.session_id,
            "title": t.title,
            "description": t.description,
            "assignee_name": t.assignee_name,
            "deadline": t.deadline,
            "status": t.status,
            "proof_description": t.proof_description,
            "proof_url": t.proof_url,
            "created_at": t.created_at,
            "updated_at": t.updated_at
        } for t in tasks
    ])


@router.post("", status_code=201)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    task = Task(
        problem_record_id=payload.problem_record_id,
        session_id=payload.session_id,
        title=payload.title,
        description=payload.description,
        assignee_name=payload.assignee_name,
        deadline=payload.deadline,
        status="todo"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        operation="task.create",
        entity_type="task",
        entity_id=task.id,
        after_state={"title": task.title, "assignee": task.assignee_name}
    )
    db.add(audit)
    await db.commit()

    return APIResponse.ok({
        "id": task.id,
        "title": task.title,
        "status": task.status
    })


@router.get("/{task_id}")
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Task).where(Task.id == task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return APIResponse.ok({
        "id": task.id,
        "problem_record_id": task.problem_record_id,
        "session_id": task.session_id,
        "title": task.title,
        "description": task.description,
        "assignee_name": task.assignee_name,
        "deadline": task.deadline,
        "status": task.status,
        "proof_description": task.proof_description,
        "proof_url": task.proof_url
    })


@router.put("/{task_id}")
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Task).where(Task.id == task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    before_state = {
        "title": task.title,
        "status": task.status,
        "assignee": task.assignee_name
    }

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.assignee_name is not None:
        task.assignee_name = payload.assignee_name
    if payload.deadline is not None:
        task.deadline = payload.deadline
    if payload.status is not None:
        task.status = payload.status
    if payload.proof_description is not None:
        task.proof_description = payload.proof_description
    if payload.proof_url is not None:
        task.proof_url = payload.proof_url

    task.updated_at = datetime.utcnow()
    await db.commit()

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        operation="task.update",
        entity_type="task",
        entity_id=task.id,
        before_state=before_state,
        after_state={
            "title": task.title,
            "status": task.status,
            "assignee": task.assignee_name
        }
    )
    db.add(audit)
    await db.commit()

    return APIResponse.ok({
        "id": task.id,
        "title": task.title,
        "status": task.status
    })


@router.delete("/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Task).where(Task.id == task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    before_state = {"title": task.title}

    await db.delete(task)
    await db.commit()

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        operation="task.delete",
        entity_type="task",
        entity_id=task_id,
        before_state=before_state
    )
    db.add(audit)
    await db.commit()

    return APIResponse.ok({"message": "Task deleted successfully"})

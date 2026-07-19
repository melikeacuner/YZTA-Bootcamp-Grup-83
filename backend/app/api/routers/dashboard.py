from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.api_envelope import APIResponse
from app.infrastructure.db.session import get_db_session
from app.infrastructure.db.models import ProblemRecordORM, ProblemSession, Task, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse:
    # 1. Update delayed tasks automatically
    now = datetime.utcnow()
    # Find all tasks that are past their deadline and not completed, mark as delayed
    active_tasks_stmt = select(Task).where(Task.status.in_(["todo", "in_progress"])).where(Task.deadline < now)
    res = await db.execute(active_tasks_stmt)
    overdue_tasks = res.scalars().all()
    for task in overdue_tasks:
        task.status = "delayed"
        task.updated_at = now
    if overdue_tasks:
        await db.commit()

    # 2. Query Statistics
    # Total Problem Records
    total_records_stmt = select(func.count(ProblemRecordORM.id))
    total_records = (await db.execute(total_records_stmt)).scalar() or 0

    # Closed Problems
    closed_records_stmt = select(func.count(ProblemRecordORM.id)).where(ProblemRecordORM.resolution_status == "closed")
    closed_records = (await db.execute(closed_records_stmt)).scalar() or 0

    # Open Problems
    open_records_stmt = select(func.count(ProblemRecordORM.id)).where(ProblemRecordORM.resolution_status == "open")
    open_records = (await db.execute(open_records_stmt)).scalar() or 0

    # Active Sessions
    active_sessions_stmt = select(func.count(ProblemSession.id)).where(ProblemSession.status == "active")
    active_sessions = (await db.execute(active_sessions_stmt)).scalar() or 0

    # Tasks Statistics
    total_tasks_stmt = select(func.count(Task.id))
    total_tasks = (await db.execute(total_tasks_stmt)).scalar() or 0

    todo_tasks = (await db.execute(select(func.count(Task.id)).where(Task.status == "todo"))).scalar() or 0
    progress_tasks = (await db.execute(select(func.count(Task.id)).where(Task.status == "in_progress"))).scalar() or 0
    completed_tasks = (await db.execute(select(func.count(Task.id)).where(Task.status == "completed"))).scalar() or 0
    delayed_tasks = (await db.execute(select(func.count(Task.id)).where(Task.status == "delayed"))).scalar() or 0

    delayed_rate = (delayed_tasks / total_tasks) if total_tasks > 0 else 0.0

    # Average RPN
    avg_rpn_stmt = select(func.avg(ProblemRecordORM.rpn))
    avg_rpn = float((await db.execute(avg_rpn_stmt)).scalar() or 0.0)

    # Department Distribution
    dept_stmt = select(ProblemRecordORM.department, func.count(ProblemRecordORM.id)).group_by(ProblemRecordORM.department)
    dept_res = (await db.execute(dept_stmt)).all()
    dept_dist = {row[0] or "Belirtilmemiş": row[1] for row in dept_res}

    # Category Distribution
    cat_stmt = select(ProblemRecordORM.problem_category, func.count(ProblemRecordORM.id)).group_by(ProblemRecordORM.problem_category)
    cat_res = (await db.execute(cat_stmt)).all()
    cat_dist = {row[0] or "Belirtilmemiş": row[1] for row in cat_res}

    # Methodology Distribution
    method_stmt = select(ProblemRecordORM.methodology, func.count(ProblemRecordORM.id)).group_by(ProblemRecordORM.methodology)
    method_res = (await db.execute(method_stmt)).all()
    method_dist = {row[0] or "Belirtilmemiş": row[1] for row in method_res}

    return APIResponse.ok({
        "total_problems": total_records,
        "closed_problems": closed_records,
        "open_problems": open_records,
        "active_sessions": active_sessions,
        "total_tasks": total_tasks,
        "todo_tasks": todo_tasks,
        "in_progress_tasks": progress_tasks,
        "completed_tasks": completed_tasks,
        "delayed_tasks": delayed_tasks,
        "delayed_rate": delayed_rate,
        "average_rpn": avg_rpn,
        "department_distribution": dept_dist,
        "category_distribution": cat_dist,
        "methodology_distribution": method_dist
    })

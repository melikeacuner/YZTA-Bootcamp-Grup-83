import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import EmbeddingStatus, MethodologyType, SessionStatus, UserRole
from app.infrastructure.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="Kullanici", nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["ProblemSession"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    problem_records: Mapped[list["ProblemRecordORM"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ProblemSession(Base):
    __tablename__ = "problem_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    methodology: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.ACTIVE.value, nullable=False)
    current_step: Mapped[int] = mapped_column(default=0, nullable=False)
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # We maintain both keys for compatibility with PKMS and legacy Grup-83 frontend code
    step_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    step_responses: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Dashboard and categorization columns
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    followup_count: Mapped[int] = mapped_column(default=0, nullable=False)
    assignee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tracker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI Agent Problem Solving columns
    agent_chat_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    agent_status: Mapped[str] = mapped_column(String(20), default="active", nullable=False) # "active", "closed"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="sessions")
    record: Mapped["ProblemRecordORM | None"] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ProblemRecordORM(Base):
    __tablename__ = "problem_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problem_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # We maintain both for compatibility
    methodology_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    step_responses: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Categorization and location metadata
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    problem_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    # FMEA Risk metrics
    severity: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    occurrence: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    detection: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    rpn: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    
    # Lean manufacturing Yokoten
    yokoten_applied: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    closure_checklist: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    resolution_status: Mapped[str] = mapped_column(String(20), default="closed", nullable=False) # "open", "closed"
    resolution_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    embedding_status: Mapped[str] = mapped_column(
        String(20), default=EmbeddingStatus.PENDING.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["ProblemSession"] = relationship(back_populates="record")
    user: Mapped["User"] = relationship(back_populates="problem_records")
    tasks: Mapped[list["Task"]] = relationship(back_populates="problem_record", cascade="all, delete-orphan")
    embedding_queue: Mapped["EmbeddingQueue | None"] = relationship(back_populates="record", uselist=False, cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # We maintain these fields for PKMS compatibility
    before_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmbeddingQueue(Base):
    __tablename__ = "embedding_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problem_records.id", ondelete="CASCADE"), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped["ProblemRecordORM"] = relationship(back_populates="embedding_queue")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("problem_records.id", ondelete="CASCADE"), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("problem_sessions.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="todo", nullable=False) # "todo", "in_progress", "completed", "delayed"
    proof_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    problem_record: Mapped["ProblemRecordORM | None"] = relationship(back_populates="tasks")
    session: Mapped["ProblemSession | None"] = relationship(back_populates="tasks")

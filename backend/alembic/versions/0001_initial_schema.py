"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default="Kullanici"),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Problem Sessions table
    op.create_table(
        "problem_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("methodology", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("problem_description", sa.Text, nullable=False),
        sa.Column("step_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("step_responses", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True, server_default="[]"),
        sa.Column("followup_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("agent_chat_history", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("agent_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Problem Records table
    op.create_table(
        "problem_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_sessions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("methodology", sa.String(20), nullable=False),
        sa.Column("methodology_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("step_responses", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("root_cause", sa.Text, nullable=True),
        sa.Column("corrective_actions", sa.Text, nullable=True),
        sa.Column("lessons_learned", sa.Text, nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("problem_category", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True, server_default="[]"),
        sa.Column("severity", sa.Integer, nullable=True, server_default="1"),
        sa.Column("occurrence", sa.Integer, nullable=True, server_default="1"),
        sa.Column("detection", sa.Integer, nullable=True, server_default="1"),
        sa.Column("rpn", sa.Integer, nullable=True, server_default="1"),
        sa.Column("yokoten_applied", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("closure_checklist", sa.JSON, nullable=True, server_default="{}"),
        sa.Column("resolution_status", sa.String(20), nullable=False, server_default="closed"),
        sa.Column("resolution_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta_data", sa.JSON, nullable=True, server_default="{}"),
        sa.Column("embedding_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("problem_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_records.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assignee_name", sa.String(255), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo"),
        sa.Column("proof_description", sa.Text, nullable=True),
        sa.Column("proof_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Embedding Queue table
    op.create_table(
        "embedding_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("before_state", sa.JSON, nullable=True),
        sa.Column("after_state", sa.JSON, nullable=True),
        sa.Column("before_values", sa.JSON, nullable=True),
        sa.Column("after_values", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("embedding_queue")
    op.drop_table("tasks")
    op.drop_table("problem_records")
    op.drop_table("problem_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

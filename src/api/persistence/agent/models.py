from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base

AGENT_SCHEMA = {"schema": "agent"}


class ConversationRow(Base):
    __tablename__ = "conversation"
    __table_args__ = AGENT_SCHEMA

    id: Mapped[UUID] = mapped_column(primary_key=True)
    person_id: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MessageRow(Base):
    __tablename__ = "message"
    __table_args__ = AGENT_SCHEMA

    id: Mapped[UUID] = mapped_column(primary_key=True)
    conversation_id: Mapped[UUID]
    position: Mapped[int]
    role: Mapped[str]
    content: Mapped[str]
    model: Mapped[str | None]
    tokens_in: Mapped[int | None]
    tokens_out: Mapped[int | None]
    latency_ms: Mapped[int | None]


class ToolCallRow(Base):
    __tablename__ = "tool_call"
    __table_args__ = AGENT_SCHEMA

    message_id: Mapped[UUID] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(primary_key=True)
    position: Mapped[int]
    name: Mapped[str]
    arguments: Mapped[dict[str, object]] = mapped_column(JSONB)
    result: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    status: Mapped[str]
    duration_ms: Mapped[int | None]

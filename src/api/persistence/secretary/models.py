from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base

SECRETARY_SCHEMA = {"schema": "secretary"}
PROTOCOL_COLUMN = "protocol"


class ProtocolRow(Base):
    __tablename__ = "protocol"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column(PROTOCOL_COLUMN, primary_key=True)
    student_id: Mapped[str | None] = mapped_column("stu_id")
    requester_type: Mapped[str]
    unit_code: Mapped[str]
    course_label: Mapped[str]
    demand: Mapped[str]
    status: Mapped[str] = mapped_column("demand_status")
    opened_at: Mapped[str]
    first_response_at: Mapped[str | None]
    due_at: Mapped[str] = mapped_column("sla_due_at")
    closed_at: Mapped[str | None]
    resolution: Mapped[str | None]


class DemandTypeRow(Base):
    __tablename__ = "demand_type"
    __table_args__ = SECRETARY_SCHEMA

    code: Mapped[str] = mapped_column("demand_code", primary_key=True)
    name: Mapped[str] = mapped_column("demand_name")
    area: Mapped[str]
    sla_hours: Mapped[str]
    fee: Mapped[str] = mapped_column("service_fee")
    active: Mapped[str]


class ProtocolHistoryRow(Base):
    __tablename__ = "protocol_status_history"
    __table_args__ = SECRETARY_SCHEMA

    protocol_id: Mapped[str] = mapped_column(PROTOCOL_COLUMN, primary_key=True)
    seq: Mapped[str] = mapped_column(primary_key=True)
    to_status: Mapped[str]
    changed_at: Mapped[str]


class ProtocolInteractionRow(Base):
    __tablename__ = "protocol_interaction"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("interaction_id", primary_key=True)
    protocol_id: Mapped[str] = mapped_column(PROTOCOL_COLUMN)
    author_type: Mapped[str]
    message: Mapped[str]
    is_internal_note: Mapped[str]
    created_at: Mapped[str]


class IssuedDocumentRow(Base):
    __tablename__ = "issued_document"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("document_id", primary_key=True)
    protocol_id: Mapped[str] = mapped_column(PROTOCOL_COLUMN)
    document_type: Mapped[str]
    issued_at: Mapped[str]
    validation_code: Mapped[str]
    delivery: Mapped[str]

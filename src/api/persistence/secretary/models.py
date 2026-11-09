from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from api.domain.protocol.catalog import ServiceArea
from api.domain.protocol.document import DocumentDelivery, DocumentType
from api.domain.protocol.message import MessageSender
from api.domain.protocol.request import Requester
from api.domain.protocol.status import ProtocolStatus, Resolution
from api.domain.shared.money import Money
from api.persistence.core.base import Base
from api.persistence.core.column_types import UtcMoment
from api.persistence.secretary import column_types

SECRETARY_SCHEMA = {"schema": "secretary"}
PROTOCOL_COLUMN = "protocol"


class ProtocolRow(Base):
    __tablename__ = "protocol"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column(PROTOCOL_COLUMN, primary_key=True)
    student_id: Mapped[str | None] = mapped_column("stu_id")
    requester_cpf: Mapped[str] = mapped_column(deferred=True, deferred_raiseload=True)
    requester_name: Mapped[str] = mapped_column(deferred=True, deferred_raiseload=True)
    requester_type: Mapped[Requester] = mapped_column(column_types.REQUESTER)
    unit_code: Mapped[str]
    course_label: Mapped[str]
    demand: Mapped[str]
    status: Mapped[ProtocolStatus] = mapped_column("demand_status", column_types.PROTOCOL_STATUS)
    channel: Mapped[str] = mapped_column(deferred=True, deferred_raiseload=True)
    priority: Mapped[str] = mapped_column(deferred=True, deferred_raiseload=True)
    opened_at: Mapped[datetime] = mapped_column(UtcMoment())
    first_response_at: Mapped[datetime | None] = mapped_column(UtcMoment())
    due_at: Mapped[datetime] = mapped_column("sla_due_at", UtcMoment())
    closed_at: Mapped[datetime | None] = mapped_column(UtcMoment())
    sla_breached: Mapped[bool] = mapped_column(
        column_types.TRUE_FALSE, deferred=True, deferred_raiseload=True
    )
    resolution: Mapped[Resolution | None] = mapped_column(column_types.RESOLUTION)


class DemandTypeRow(Base):
    __tablename__ = "demand_type"
    __table_args__ = SECRETARY_SCHEMA

    code: Mapped[str] = mapped_column("demand_code", primary_key=True)
    name: Mapped[str] = mapped_column("demand_name")
    area: Mapped[ServiceArea] = mapped_column(column_types.SERVICE_AREA)
    sla_hours: Mapped[str]
    fee: Mapped[Money] = mapped_column("service_fee", column_types.ServiceFee())
    active: Mapped[bool] = mapped_column(column_types.TRUE_FALSE)


class ProtocolHistoryRow(Base):
    __tablename__ = "protocol_status_history"
    __table_args__ = SECRETARY_SCHEMA

    protocol_id: Mapped[str] = mapped_column(PROTOCOL_COLUMN, primary_key=True)
    seq: Mapped[str] = mapped_column(primary_key=True)
    to_status: Mapped[ProtocolStatus] = mapped_column(column_types.PROTOCOL_STATUS)
    changed_at: Mapped[datetime] = mapped_column(UtcMoment())
    changed_by: Mapped[str] = mapped_column(deferred=True, deferred_raiseload=True)


class ProtocolInteractionRow(Base):
    __tablename__ = "protocol_interaction"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("interaction_id", primary_key=True)
    protocol_id: Mapped[str] = mapped_column(PROTOCOL_COLUMN)
    author_type: Mapped[MessageSender] = mapped_column(column_types.SENDER)
    author: Mapped[str] = mapped_column(deferred=True, deferred_raiseload=True)
    message: Mapped[str]
    is_internal_note: Mapped[bool] = mapped_column(column_types.TRUE_FALSE)
    created_at: Mapped[datetime] = mapped_column(UtcMoment())


class IssuedDocumentRow(Base):
    __tablename__ = "issued_document"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("document_id", primary_key=True)
    protocol_id: Mapped[str] = mapped_column(PROTOCOL_COLUMN)
    document_type: Mapped[DocumentType] = mapped_column(column_types.DOCUMENT_TYPE)
    issued_at: Mapped[datetime] = mapped_column(UtcMoment())
    validation_code: Mapped[str]
    delivery: Mapped[DocumentDelivery] = mapped_column(column_types.DOCUMENT_DELIVERY)

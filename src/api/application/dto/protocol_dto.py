from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.dto.protocol_service_dto import ServiceDto
from api.domain.invoice import Invoice, InvoiceStatus
from api.domain.protocol import Protocol, Requester
from api.domain.protocol_catalog import Service
from api.domain.protocol_document import DocumentDelivery, DocumentType, ProtocolDocument
from api.domain.protocol_status import DeadlineSituation, ProtocolStatus, Resolution


class ProtocolDocumentDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    type: DocumentType
    issued_at: datetime
    validation_code: str
    delivery: DocumentDelivery

    @classmethod
    def from_entity(cls, document: ProtocolDocument) -> Self:
        return cls(
            id=document.id,
            type=document.type,
            issued_at=document.issued_at,
            validation_code=document.validation_code,
            delivery=document.delivery,
        )


class FeeInvoiceDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_id: str
    due_date: date
    status: InvoiceStatus
    balance_reais: Decimal
    is_paid: bool

    @classmethod
    def from_entity(cls, invoice: Invoice) -> Self:
        return cls(
            invoice_id=invoice.id,
            due_date=invoice.due_date,
            status=invoice.status,
            balance_reais=invoice.balance.reais,
            is_paid=invoice.status is InvoiceStatus.PAID,
        )


class ProtocolFeeDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount_reais: Decimal
    invoice: FeeInvoiceDto | None

    @classmethod
    def of(cls, service: Service, invoice: Invoice | None) -> Self | None:
        if not service.has_fee:
            return None
        return cls(
            amount_reais=service.fee.reais,
            invoice=None if invoice is None else FeeInvoiceDto.from_entity(invoice),
        )


class ProtocolDeadlineDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    due_at: datetime
    sla_hours: int
    situation: DeadlineSituation


class ProtocolDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: str
    service: ServiceDto
    status: ProtocolStatus
    resolution: Resolution | None
    opened_by: Requester
    enrollment: str | None
    course_label: str
    opened_at: datetime
    status_since: datetime | None
    first_response_at: datetime | None
    closed_at: datetime | None
    deadline: ProtocolDeadlineDto
    fee: ProtocolFeeDto | None
    documents: tuple[ProtocolDocumentDto, ...]

    @classmethod
    def from_entity(cls, protocol: Protocol, reference: date, fee_invoice: Invoice | None) -> Self:
        return cls(
            number=protocol.number,
            service=ServiceDto.from_entity(protocol.service),
            status=protocol.status,
            resolution=protocol.resolution,
            opened_by=protocol.requester,
            enrollment=protocol.enrollment_reference,
            course_label=protocol.course_label,
            opened_at=protocol.opened_at,
            status_since=protocol.status_since,
            first_response_at=protocol.first_response_at,
            closed_at=protocol.closed_at,
            deadline=ProtocolDeadlineDto(
                due_at=protocol.due_at,
                sla_hours=protocol.service.sla_hours,
                situation=protocol.deadline(reference),
            ),
            fee=ProtocolFeeDto.of(protocol.service, fee_invoice),
            documents=tuple(ProtocolDocumentDto.from_entity(item) for item in protocol.documents),
        )

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from api.domain.protocol.catalog import Service
from api.domain.protocol.document import ProtocolDocument
from api.domain.protocol.message import ProtocolMessage
from api.domain.protocol.status import (
    STATUS_STAGE,
    DeadlineSituation,
    ProtocolStage,
    ProtocolStatus,
    ProtocolStatusChange,
    Resolution,
)
from api.domain.shared.brand import Brand, Modality


class Requester(Enum):
    SELF = "self"
    GUARDIAN = "guardian"


@dataclass(frozen=True, slots=True)
class Protocol:
    number: str
    service: Service
    status: ProtocolStatus
    resolution: Resolution | None
    requester: Requester
    brand: Brand
    modality: Modality
    enrollment_reference: str | None
    course_label: str
    opened_at: datetime
    first_response_at: datetime | None
    due_at: datetime
    closed_at: datetime | None
    documents: tuple[ProtocolDocument, ...]
    history: tuple[ProtocolStatusChange, ...]
    messages: tuple[ProtocolMessage, ...]

    @property
    def stage(self) -> ProtocolStage:
        return STATUS_STAGE[self.status]

    @property
    def is_in_progress(self) -> bool:
        return self.stage is ProtocolStage.IN_PROGRESS

    @property
    def status_since(self) -> datetime | None:
        return self.history[-1].changed_at if self.history else None

    def deadline(self, reference: date) -> DeadlineSituation:
        if self.closed_at is not None:
            return (
                DeadlineSituation.MET if self.closed_at <= self.due_at else DeadlineSituation.MISSED
            )
        if reference > self.due_at.date():
            return DeadlineSituation.OVERDUE
        return DeadlineSituation.WITHIN_DEADLINE

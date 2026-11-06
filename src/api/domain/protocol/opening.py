from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Self

from api.domain.academic.enrollment import Enrollment
from api.domain.protocol.catalog import Service
from api.domain.protocol.errors import DuplicateProtocolError, ServiceNotOpenableError
from api.domain.protocol.proposal import ProposalRules
from api.domain.protocol.request import Protocol
from api.domain.protocol.status import ProtocolStatus, ProtocolStatusChange

BRASILIA = timezone(timedelta(hours=-3), "America/Sao_Paulo")


@dataclass(frozen=True, slots=True)
class OpeningRequest:
    requester_name: str = field(repr=False)
    message: str = field(repr=False)
    today: date


@dataclass(frozen=True, slots=True)
class ProtocolOpening:
    service_code: str
    enrollment_reference: str
    unit_name: str
    course_name: str
    requester_name: str = field(repr=False)
    message: str = field(repr=False)
    status: ProtocolStatus
    opened_at: datetime
    due_at: datetime

    @classmethod
    def open(
        cls,
        service: Service,
        enrollment: Enrollment,
        existing: Iterable[Protocol],
        request: OpeningRequest,
    ) -> Self:
        reason = ProposalRules.refusal(service, request.message)
        if reason is not None:
            raise ServiceNotOpenableError(reason)
        if ProposalRules.duplicate_of(existing, service, enrollment) is not None:
            raise DuplicateProtocolError
        opened_at = datetime.combine(request.today, time.min, BRASILIA)
        return cls(
            service_code=service.code,
            enrollment_reference=enrollment.reference,
            unit_name=enrollment.unit_name,
            course_name=enrollment.course_name,
            requester_name=request.requester_name,
            message=request.message,
            status=ProtocolStatus.OPEN,
            opened_at=opened_at,
            due_at=opened_at + timedelta(hours=service.sla_hours),
        )

    @property
    def first_change(self) -> ProtocolStatusChange:
        return ProtocolStatusChange(status=self.status, changed_at=self.opened_at)

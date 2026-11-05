from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.dto.protocol_service_dto import ServiceDto
from api.domain.academic import Enrollment
from api.domain.protocol_catalog import Service
from api.domain.protocol_proposal import RefusalReason


class ProtocolProposalDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    service: ServiceDto
    enrollment: str
    course_name: str
    message: str
    requires_confirmation: bool

    @classmethod
    def of(cls, service: Service, enrollment: Enrollment, message: str) -> Self:
        return cls(
            service=ServiceDto.from_entity(service),
            enrollment=enrollment.reference,
            course_name=enrollment.course_name,
            message=message,
            requires_confirmation=True,
        )


class ProtocolRefusalDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: RefusalReason
    service: ServiceDto
    existing_protocol: str | None = None

    @classmethod
    def of(cls, reason: RefusalReason, service: Service, existing: str | None = None) -> Self:
        return cls(
            reason=reason, service=ServiceDto.from_entity(service), existing_protocol=existing
        )


type Proposal = ProtocolProposalDto | ProtocolRefusalDto

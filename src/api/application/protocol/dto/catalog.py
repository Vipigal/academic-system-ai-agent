from collections.abc import Sequence
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.academic.enrollment import Enrollment, EnrollmentStatus
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.availability import ServiceAvailability, Unavailability
from api.domain.protocol.catalog import Service, ServiceArea

STATUS_SEPARATOR = ", "
UNAVAILABLE_REASONS = {
    Unavailability.SERVICE_INACTIVE: "O serviço está inativo.",
    Unavailability.SERVICE_HAS_FEE: "Tem taxa: o aluno pede este serviço com a secretaria.",
    Unavailability.HANDLED_BY_SECRETARY: "O agente não abre este serviço: o aluno pede com a "
    "secretaria.",
    Unavailability.ENROLLMENT_STATUS: "Aceita só matrícula com situação {accepted}, e nenhuma "
    "matrícula do aluno está assim.",
}


class ServiceDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str
    title: str | None
    effect: str | None
    area: ServiceArea
    sla_hours: int
    fee_reais: Decimal
    active: bool

    @classmethod
    def from_entity(cls, service: Service) -> Self:
        entry = ServiceActions.find(service.code)
        return cls(
            code=service.code,
            name=service.name,
            title=None if entry is None else entry.title,
            effect=None if entry is None else entry.effect,
            area=service.area,
            sla_hours=service.sla_hours,
            fee_reais=service.fee.reais,
            active=service.active,
        )


class ServiceOfferDto(ServiceDto):
    available: bool
    unavailable_reason: str | None

    @classmethod
    def of(cls, service: Service, enrollments: Sequence[Enrollment]) -> Self:
        unavailability = ServiceAvailability.of(service, enrollments)
        return cls(
            **ServiceDto.from_entity(service).model_dump(),
            available=unavailability is None,
            unavailable_reason=cls._reason(service, unavailability),
        )

    @staticmethod
    def _reason(service: Service, unavailability: Unavailability | None) -> str | None:
        if unavailability is None:
            return None
        entry = ServiceActions.find(service.code)
        accepted = () if entry is None else entry.accepted_statuses
        names = (item.value for item in EnrollmentStatus if item in accepted)
        return UNAVAILABLE_REASONS[unavailability].format(accepted=STATUS_SEPARATOR.join(names))

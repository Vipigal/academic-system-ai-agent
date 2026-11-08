from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.catalog import Service, ServiceArea


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
    agent_can_open: bool

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
            agent_can_open=service.agent_can_open,
        )

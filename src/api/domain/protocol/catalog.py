from dataclasses import dataclass
from enum import Enum

from api.domain.protocol.action_catalog import ServiceActions
from api.domain.shared.money import Money


class ServiceArea(Enum):
    ACADEMIC = "academic"
    DOCUMENTS = "documents"
    FINANCIAL = "financial"
    GENERAL = "general"
    OMBUDSMAN = "ombudsman"
    TECH = "tech"


@dataclass(frozen=True, slots=True)
class Service:
    code: str
    name: str
    area: ServiceArea
    sla_hours: int
    fee: Money
    active: bool

    @property
    def has_fee(self) -> bool:
        return self.fee.cents > 0

    @property
    def agent_can_open(self) -> bool:
        proposable = ServiceActions.proposable(self.code) is not None
        return proposable and self.active and not self.has_fee

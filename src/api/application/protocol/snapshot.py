from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from api.application.protocol.dto.detail import ProtocolDetailDto
from api.application.protocol.dto.request import ProtocolDto
from api.domain.finance.invoice import Invoice
from api.domain.protocol.request import Protocol
from api.domain.protocol.status import DeadlineSituation


@dataclass(frozen=True, slots=True)
class ProtocolSnapshot:
    protocols: Sequence[Protocol]
    fees: Mapping[str, Invoice]
    today: date

    def dtos(self, protocols: Sequence[Protocol]) -> list[ProtocolDto]:
        return [
            ProtocolDto.from_entity(item, self.today, self.fees.get(item.number))
            for item in protocols
        ]

    def detail(self, protocol: Protocol) -> ProtocolDetailDto:
        return ProtocolDetailDto.from_entity(protocol, self.today, self.fees.get(protocol.number))

    def totals(self, protocols: Sequence[Protocol]) -> dict[str, int]:
        overdue = [item for item in protocols if self._is_overdue(item)]
        return {
            "in_progress": sum(item.is_in_progress for item in protocols),
            "overdue": len(overdue),
        }

    def _is_overdue(self, protocol: Protocol) -> bool:
        return protocol.deadline(self.today) is DeadlineSituation.OVERDUE

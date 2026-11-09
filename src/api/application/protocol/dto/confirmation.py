from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.protocol.opening import ProtocolOpening
from api.domain.protocol.status import ProtocolStatus


class ConfirmedProtocolDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    protocol_number: str
    status: ProtocolStatus
    sla_due_at: datetime

    @classmethod
    def of(cls, number: str, opening: ProtocolOpening) -> Self:
        return cls(protocol_number=number, status=opening.status, sla_due_at=opening.due_at)

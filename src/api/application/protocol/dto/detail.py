from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.protocol.dto.request import ProtocolDto
from api.domain.finance.invoice import Invoice
from api.domain.protocol.message import MessageSender, ProtocolMessage
from api.domain.protocol.request import Protocol
from api.domain.protocol.status import ProtocolStatus, ProtocolStatusChange


class ProtocolStatusChangeDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ProtocolStatus
    changed_at: datetime

    @classmethod
    def from_entity(cls, change: ProtocolStatusChange) -> Self:
        return cls(status=change.status, changed_at=change.changed_at)


class ProtocolMessageDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    sender: MessageSender
    text: str
    created_at: datetime

    @classmethod
    def from_entity(cls, message: ProtocolMessage) -> Self:
        return cls(sender=message.sender, text=message.text, created_at=message.created_at)


class ProtocolDetailDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    protocol: ProtocolDto
    history: tuple[ProtocolStatusChangeDto, ...]
    messages: tuple[ProtocolMessageDto, ...]

    @classmethod
    def from_entity(cls, protocol: Protocol, reference: date, fee_invoice: Invoice | None) -> Self:
        return cls(
            protocol=ProtocolDto.from_entity(protocol, reference, fee_invoice),
            history=tuple(ProtocolStatusChangeDto.from_entity(item) for item in protocol.history),
            messages=tuple(ProtocolMessageDto.from_entity(item) for item in protocol.messages),
        )

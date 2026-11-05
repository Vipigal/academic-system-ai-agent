from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.dto.protocol_dto import ProtocolDto
from api.domain.invoice import Invoice
from api.domain.protocol import Protocol
from api.domain.protocol_message import MessageSender, ProtocolMessage
from api.domain.protocol_status import ProtocolStatus, ProtocolStatusChange


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

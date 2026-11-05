from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MessageSender(Enum):
    REQUESTER = "requester"
    SECRETARIAT = "secretariat"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class ProtocolMessage:
    id: str
    sender: MessageSender
    text: str
    created_at: datetime

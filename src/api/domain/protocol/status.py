from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProtocolStatus(Enum):
    OPEN = "open"
    IN_ANALYSIS = "in_analysis"
    PENDING_REQUESTER = "pending_requester"
    REOPENED = "reopened"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ProtocolStage(Enum):
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class Resolution(Enum):
    GRANTED = "granted"
    DENIED = "denied"
    DUPLICATE = "duplicate"
    WITHDRAWN = "withdrawn"


class DeadlineSituation(Enum):
    WITHIN_DEADLINE = "within_deadline"
    OVERDUE = "overdue"
    MET = "met"
    MISSED = "missed"


STATUS_STAGE = {
    ProtocolStatus.OPEN: ProtocolStage.IN_PROGRESS,
    ProtocolStatus.IN_ANALYSIS: ProtocolStage.IN_PROGRESS,
    ProtocolStatus.PENDING_REQUESTER: ProtocolStage.IN_PROGRESS,
    ProtocolStatus.REOPENED: ProtocolStage.IN_PROGRESS,
    ProtocolStatus.RESOLVED: ProtocolStage.RESOLVED,
    ProtocolStatus.CANCELLED: ProtocolStage.CANCELLED,
}


@dataclass(frozen=True, slots=True)
class ProtocolStatusChange:
    status: ProtocolStatus
    changed_at: datetime

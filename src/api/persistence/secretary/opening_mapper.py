from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func

from api.domain.protocol.message import MessageSender
from api.domain.protocol.opening import ProtocolOpening
from api.domain.protocol.request import Requester
from api.persistence.core.base import Base
from api.persistence.secretary.dialect import SecretaryDialect
from api.persistence.secretary.models import (
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)

PROTOCOL_SEQUENCE = "agent.protocol_number_seq"
INTERACTION_SEQUENCE = "agent.protocol_interaction_seq"
PORTAL_CHANNEL = "Portal"
NORMAL_PRIORITY = "Normal"
FIRST_CHANGE = "1"
SYSTEM_AUTHOR = "system"


@dataclass(frozen=True, slots=True)
class OpeningRows:
    protocol: ProtocolRow
    history: ProtocolHistoryRow
    interaction: ProtocolInteractionRow

    @property
    def steps(self) -> tuple[Sequence[Base], ...]:
        return [self.protocol], [self.history], [self.interaction]


class ProtocolOpeningMapper:
    @classmethod
    def rows(cls, opening: ProtocolOpening, student_id: str, cpf: str) -> OpeningRows:
        return OpeningRows(
            cls._protocol(opening, student_id, cpf),
            cls._history(opening),
            cls._interaction(opening),
        )

    @classmethod
    def _protocol(cls, opening: ProtocolOpening, student_id: str, cpf: str) -> ProtocolRow:
        return ProtocolRow(
            id=func.nextval(PROTOCOL_SEQUENCE),
            student_id=student_id,
            requester_cpf=cpf,
            requester_name=opening.requester_name,
            requester_type=Requester.SELF,
            unit_code=SecretaryDialect.unit_code(opening.unit_name),
            course_label=opening.course_name,
            demand=opening.service_code,
            status=opening.status,
            channel=PORTAL_CHANNEL,
            priority=NORMAL_PRIORITY,
            opened_at=opening.opened_at,
            due_at=opening.due_at,
            sla_breached=False,
        )

    @classmethod
    def _history(cls, opening: ProtocolOpening) -> ProtocolHistoryRow:
        change = opening.first_change
        return ProtocolHistoryRow(
            protocol_id=func.currval(PROTOCOL_SEQUENCE),
            seq=FIRST_CHANGE,
            to_status=change.status,
            changed_at=change.changed_at,
            changed_by=SYSTEM_AUTHOR,
        )

    @classmethod
    def _interaction(cls, opening: ProtocolOpening) -> ProtocolInteractionRow:
        return ProtocolInteractionRow(
            id=func.nextval(INTERACTION_SEQUENCE),
            protocol_id=func.currval(PROTOCOL_SEQUENCE),
            author_type=MessageSender.REQUESTER,
            author=opening.requester_name,
            message=opening.message,
            is_internal_note=False,
            created_at=opening.opened_at,
        )

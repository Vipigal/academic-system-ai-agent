from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func

from api.domain.protocol.opening import ProtocolOpening
from api.persistence.core.base import Base
from api.persistence.secretary.dialect import SecretaryDialect
from api.persistence.secretary.models import (
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)
from api.persistence.secretary.vocabulary import ProtocolVocabulary

PROTOCOL_SEQUENCE = "agent.protocol_number_seq"
INTERACTION_SEQUENCE = "agent.protocol_interaction_seq"
SOURCE_MOMENT = "%Y-%m-%dT%H:%M:%SZ"
STUDENT_REQUESTER = "Student"
PORTAL_CHANNEL = "Portal"
NORMAL_PRIORITY = "Normal"
FALSE_FLAG = "False"
FIRST_CHANGE = "1"
SYSTEM_AUTHOR = "system"
REQUESTER_AUTHOR = "Requester"


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
            requester_type=STUDENT_REQUESTER,
            unit_code=SecretaryDialect.unit_code(opening.unit_name),
            course_label=opening.course_name,
            demand=opening.service_code,
            status=ProtocolVocabulary.source_of_status(opening.status),
            channel=PORTAL_CHANNEL,
            priority=NORMAL_PRIORITY,
            opened_at=cls._moment(opening.opened_at),
            due_at=cls._moment(opening.due_at),
            sla_breached=FALSE_FLAG,
        )

    @classmethod
    def _history(cls, opening: ProtocolOpening) -> ProtocolHistoryRow:
        change = opening.first_change
        return ProtocolHistoryRow(
            protocol_id=func.currval(PROTOCOL_SEQUENCE),
            seq=FIRST_CHANGE,
            to_status=ProtocolVocabulary.source_of_status(change.status),
            changed_at=cls._moment(change.changed_at),
            changed_by=SYSTEM_AUTHOR,
        )

    @classmethod
    def _interaction(cls, opening: ProtocolOpening) -> ProtocolInteractionRow:
        return ProtocolInteractionRow(
            id=func.nextval(INTERACTION_SEQUENCE),
            protocol_id=func.currval(PROTOCOL_SEQUENCE),
            author_type=REQUESTER_AUTHOR,
            author=opening.requester_name,
            message=opening.message,
            is_internal_note=FALSE_FLAG,
            created_at=cls._moment(opening.opened_at),
        )

    @staticmethod
    def _moment(value: datetime) -> str:
        return value.astimezone(UTC).strftime(SOURCE_MOMENT)

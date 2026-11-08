import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Self

from api.domain.academic.enrollment import Enrollment
from api.domain.identity.session import StudentSession
from api.domain.protocol.action import ServiceAction
from api.domain.protocol.catalog import Service
from api.domain.protocol.request import Protocol

NOT_A_DIGIT = re.compile(r"\D")


class RefusalReason(Enum):
    SERVICE_HAS_FEE = "service_has_fee"
    SERVICE_INACTIVE = "service_inactive"
    EMPTY_MESSAGE = "empty_message"
    DUPLICATE_IN_PROGRESS = "duplicate_in_progress"
    SUBJECT_NOT_SUPPORTED = "subject_not_supported"
    ENROLLMENT_STATUS = "enrollment_status"


@dataclass(frozen=True, slots=True)
class SignedProposal:
    person_id: str
    enrollment: str
    service_code: str

    @classmethod
    def of(cls, session: StudentSession, service: Service, enrollment: Enrollment) -> Self:
        return cls(min(session.person_ids), enrollment.reference, service.code)


class ProtocolNumber:
    @staticmethod
    def digits(number: str) -> str:
        return NOT_A_DIGIT.sub("", number)


class ProposalRules:
    @staticmethod
    def refusal(service: Service) -> RefusalReason | None:
        if not service.active:
            return RefusalReason.SERVICE_INACTIVE
        if service.has_fee:
            return RefusalReason.SERVICE_HAS_FEE
        return None

    @staticmethod
    def action_refusal(action: ServiceAction, subject: str | None) -> RefusalReason | None:
        if subject is not None and not action.accepts_subject:
            return RefusalReason.SUBJECT_NOT_SUPPORTED
        return None

    @staticmethod
    def enrollment_refusal(action: ServiceAction, enrollment: Enrollment) -> RefusalReason | None:
        if not action.accepts(enrollment.status):
            return RefusalReason.ENROLLMENT_STATUS
        return None

    @staticmethod
    def message_refusal(message: str) -> RefusalReason | None:
        if not message.strip():
            return RefusalReason.EMPTY_MESSAGE
        return None

    @staticmethod
    def duplicate_of(
        protocols: Iterable[Protocol], service: Service, enrollment: Enrollment
    ) -> Protocol | None:
        return next(
            (
                protocol
                for protocol in protocols
                if protocol.is_in_progress
                and protocol.service.code == service.code
                and ProposalRules._same_enrollment(protocol, enrollment)
            ),
            None,
        )

    @staticmethod
    def _same_enrollment(protocol: Protocol, enrollment: Enrollment) -> bool:
        if protocol.enrollment_reference is not None:
            return protocol.enrollment_reference == enrollment.reference
        return (protocol.brand, protocol.modality) == (enrollment.brand, enrollment.modality)

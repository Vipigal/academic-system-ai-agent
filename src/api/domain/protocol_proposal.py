import re
from collections.abc import Iterable
from enum import Enum

from api.domain.academic import Enrollment
from api.domain.protocol import Protocol
from api.domain.protocol_catalog import Service

NOT_A_DIGIT = re.compile(r"\D")


class RefusalReason(Enum):
    SERVICE_HAS_FEE = "service_has_fee"
    SERVICE_INACTIVE = "service_inactive"
    EMPTY_MESSAGE = "empty_message"
    DUPLICATE_IN_PROGRESS = "duplicate_in_progress"


class ProtocolNumber:
    @staticmethod
    def digits(number: str) -> str:
        return NOT_A_DIGIT.sub("", number)


class ProposalRules:
    @staticmethod
    def refusal(service: Service, message: str) -> RefusalReason | None:
        if not service.active:
            return RefusalReason.SERVICE_INACTIVE
        if service.has_fee:
            return RefusalReason.SERVICE_HAS_FEE
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

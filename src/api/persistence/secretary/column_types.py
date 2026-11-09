import re
from typing import override

from api.domain.protocol.catalog import ServiceArea
from api.domain.protocol.document import DocumentDelivery, DocumentType
from api.domain.protocol.message import MessageSender
from api.domain.protocol.request import Requester
from api.domain.protocol.status import ProtocolStatus, Resolution
from api.domain.shared.money import Money
from api.persistence.core.column_types import SourceText, TextFlag
from api.persistence.core.source_enum import SourceEnum

NOT_A_DIGIT = re.compile(r"\D")
REAL_SEPARATORS = str.maketrans(",.", ".,")
TRUE_FALSE = TextFlag("True", "False")
SERVICE_AREA = SourceEnum.by_name(ServiceArea)
PROTOCOL_STATUS = SourceEnum(
    {
        "Open": ProtocolStatus.OPEN,
        "In Analysis": ProtocolStatus.IN_ANALYSIS,
        "Pending Requester": ProtocolStatus.PENDING_REQUESTER,
        "Reopened": ProtocolStatus.REOPENED,
        "Resolved": ProtocolStatus.RESOLVED,
        "Cancelled": ProtocolStatus.CANCELLED,
    }
)
RESOLUTION = SourceEnum(
    {
        "Granted": Resolution.GRANTED,
        "Denied": Resolution.DENIED,
        "Duplicate": Resolution.DUPLICATE,
        "Withdrawn": Resolution.WITHDRAWN,
    }
)
REQUESTER = SourceEnum(
    {
        "Student": Requester.SELF,
        "Alumni": Requester.SELF,
        "Guardian": Requester.GUARDIAN,
    }
)
SENDER = SourceEnum(
    {
        "Requester": MessageSender.REQUESTER,
        "Analyst": MessageSender.SECRETARIAT,
        "System": MessageSender.SYSTEM,
    }
)
DOCUMENT_TYPE = SourceEnum(
    {
        "Diploma": DocumentType.DIPLOMA,
        "Completion Certificate": DocumentType.COMPLETION_CERTIFICATE,
        "Transcript": DocumentType.TRANSCRIPT,
        "Syllabus": DocumentType.SYLLABUS,
        "Enrollment Certificate": DocumentType.ENROLLMENT_CERTIFICATE,
    }
)
DOCUMENT_DELIVERY = SourceEnum(
    {
        "Digital": DocumentDelivery.DIGITAL,
        "Printed": DocumentDelivery.PRINTED,
    }
)


class ServiceFee(SourceText[Money]):
    cache_ok = True

    @override
    def to_source(self, value: Money) -> str:
        amount = format(value.reais, ",.2f").translate(REAL_SEPARATORS)
        return f"R$ {amount}"

    @override
    def from_source(self, text: str) -> Money:
        return Money(int(NOT_A_DIGIT.sub("", text)))

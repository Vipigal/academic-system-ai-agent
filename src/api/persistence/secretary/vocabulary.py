import re

from api.domain.protocol.catalog import ServiceArea
from api.domain.protocol.document import DocumentDelivery, DocumentType
from api.domain.protocol.message import MessageSender
from api.domain.protocol.request import Requester
from api.domain.protocol.status import ProtocolStatus, Resolution
from api.domain.shared.brand import Brand, Modality
from api.domain.shared.money import Money
from api.persistence.core.dialect_lookup import DialectLookup
from api.persistence.sag.dialect import BRAND_BY_SOURCE, ONLINE_SUFFIX, SagDialect
from api.persistence.secretary.dialect import UNIT_PREFIX_BY_BRAND

NOT_A_DIGIT = re.compile(r"\D")
STUDENT_ID_WIDTH = 6
UNIT_SEPARATOR = "-"
YES = "True"
BRAND_BY_UNIT_PREFIX = {prefix: brand for brand, prefix in UNIT_PREFIX_BY_BRAND.items()}
SOURCE_BY_BRAND = {brand: source for source, brand in BRAND_BY_SOURCE.items()}
AREA_BY_SOURCE = {
    "ACADEMIC": ServiceArea.ACADEMIC,
    "DOCUMENTS": ServiceArea.DOCUMENTS,
    "FINANCIAL": ServiceArea.FINANCIAL,
    "GENERAL": ServiceArea.GENERAL,
    "OMBUDSMAN": ServiceArea.OMBUDSMAN,
    "TECH": ServiceArea.TECH,
}
STATUS_BY_SOURCE = {
    "Open": ProtocolStatus.OPEN,
    "In Analysis": ProtocolStatus.IN_ANALYSIS,
    "Pending Requester": ProtocolStatus.PENDING_REQUESTER,
    "Reopened": ProtocolStatus.REOPENED,
    "Resolved": ProtocolStatus.RESOLVED,
    "Cancelled": ProtocolStatus.CANCELLED,
}
RESOLUTION_BY_SOURCE = {
    "Granted": Resolution.GRANTED,
    "Denied": Resolution.DENIED,
    "Duplicate": Resolution.DUPLICATE,
    "Withdrawn": Resolution.WITHDRAWN,
}
REQUESTER_BY_SOURCE = {
    "Student": Requester.SELF,
    "Alumni": Requester.SELF,
    "Guardian": Requester.GUARDIAN,
}
SENDER_BY_SOURCE = {
    "Requester": MessageSender.REQUESTER,
    "Analyst": MessageSender.SECRETARIAT,
    "System": MessageSender.SYSTEM,
}
DOCUMENT_TYPE_BY_SOURCE = {
    "Diploma": DocumentType.DIPLOMA,
    "Completion Certificate": DocumentType.COMPLETION_CERTIFICATE,
    "Transcript": DocumentType.TRANSCRIPT,
    "Syllabus": DocumentType.SYLLABUS,
    "Enrollment Certificate": DocumentType.ENROLLMENT_CERTIFICATE,
}
DELIVERY_BY_SOURCE = {
    "Digital": DocumentDelivery.DIGITAL,
    "Printed": DocumentDelivery.PRINTED,
}


class ProtocolVocabulary:
    @staticmethod
    def status(source: str) -> ProtocolStatus:
        return DialectLookup.find(STATUS_BY_SOURCE, source, "demand_status")

    @staticmethod
    def resolution(source: str | None) -> Resolution | None:
        if source is None:
            return None
        return DialectLookup.find(RESOLUTION_BY_SOURCE, source, "resolution")

    @staticmethod
    def requester(source: str) -> Requester:
        return DialectLookup.find(REQUESTER_BY_SOURCE, source, "requester_type")

    @staticmethod
    def sender(source: str) -> MessageSender:
        return DialectLookup.find(SENDER_BY_SOURCE, source, "author_type")


class DocumentVocabulary:
    @staticmethod
    def document_type(source: str) -> DocumentType:
        return DialectLookup.find(DOCUMENT_TYPE_BY_SOURCE, source, "document_type")

    @staticmethod
    def delivery(source: str) -> DocumentDelivery:
        return DialectLookup.find(DELIVERY_BY_SOURCE, source, "delivery")


class ServiceVocabulary:
    @staticmethod
    def area(source: str) -> ServiceArea:
        return DialectLookup.find(AREA_BY_SOURCE, source, "demand area")

    @staticmethod
    def fee(source: str) -> Money:
        return Money.from_cents(int(NOT_A_DIGIT.sub("", source)))

    @staticmethod
    def is_active(source: str) -> bool:
        return source == YES


class UnitVocabulary:
    @staticmethod
    def unit(unit_code: str) -> tuple[Brand, Modality]:
        prefix = unit_code.split(UNIT_SEPARATOR, maxsplit=1)[0]
        brand = DialectLookup.find(BRAND_BY_UNIT_PREFIX, prefix, "unit_code")
        online = unit_code.endswith(f"{UNIT_SEPARATOR}EAD")
        return brand, Modality.ONLINE if online else Modality.IN_PERSON

    @classmethod
    def enrollment_reference(cls, unit_code: str, student_id: str | None) -> str | None:
        if not student_id:
            return None
        brand, modality = cls.unit(unit_code)
        suffix = ONLINE_SUFFIX if modality is Modality.ONLINE else ""
        source = f"{SOURCE_BY_BRAND[brand]}{suffix}"
        return SagDialect.reference(source, student_id.zfill(STUDENT_ID_WIDTH))

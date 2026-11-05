from decimal import Decimal

from api.domain.academic import EnrollmentStatus, Shift, TermStatus
from api.domain.academic_record import Delivery, SubjectResult
from api.domain.brand import Modality
from api.persistence.dialect_lookup import DialectLookup

YES = "Y"
MODALITY_BY_SOURCE = {"CAMPUS": Modality.IN_PERSON, "DL": Modality.ONLINE}
SHIFT_BY_SOURCE = {shift.name: shift for shift in Shift}
ENROLLMENT_STATUS_BY_SOURCE = {status.name: status for status in EnrollmentStatus}
TERM_STATUS_BY_SOURCE = {status.name: status for status in TermStatus}
RESULT_BY_SOURCE = {result.name: result for result in SubjectResult}
DELIVERY_BY_SOURCE = {delivery.name: delivery for delivery in Delivery}


class AcademicVocabulary:
    @staticmethod
    def modality(source: str) -> Modality:
        return DialectLookup.find(MODALITY_BY_SOURCE, source, "modality")

    @staticmethod
    def shift(source: str) -> Shift:
        return DialectLookup.find(SHIFT_BY_SOURCE, source, "shift")

    @staticmethod
    def enrollment_status(source: str) -> EnrollmentStatus:
        return DialectLookup.find(ENROLLMENT_STATUS_BY_SOURCE, source, "enrollment_status")

    @staticmethod
    def term_status(source: str) -> TermStatus:
        return DialectLookup.find(TERM_STATUS_BY_SOURCE, source, "term_status")

    @staticmethod
    def result(source: str) -> SubjectResult:
        return DialectLookup.find(RESULT_BY_SOURCE, source, "result")

    @staticmethod
    def delivery(source: str) -> Delivery:
        return DialectLookup.find(DELIVERY_BY_SOURCE, source, "delivery")


class SourceColumn:
    @staticmethod
    def is_yes(flag: str) -> bool:
        return flag == YES

    @staticmethod
    def decimal(value: str | None) -> Decimal | None:
        return None if value is None else Decimal(value)

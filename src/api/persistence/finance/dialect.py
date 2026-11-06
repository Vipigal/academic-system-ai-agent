from collections.abc import Collection

from sqlalchemy import ColumnElement, func, tuple_

from api.domain.finance.invoice import InvoiceStatus
from api.domain.shared.brand import STUDENT_NUMBER_LENGTH, Brand, EnrollmentRef, Modality
from api.persistence.core.dialect_lookup import DialectLookup
from api.persistence.finance.models import ContractRow

COMPANY_BY_BRAND = {
    Brand.SAO_PAULO: "1010",
    Brand.MONTANHAS: "1020",
    Brand.LITORAL: "1030",
    Brand.ATLANTICO: "1040",
    Brand.ARAUCARIA: "1050",
}
AREA_BY_MODALITY = {Modality.IN_PERSON: "PRESENCIAL", Modality.ONLINE: "DIGITAL"}
STATUS_BY_SOURCE = {
    "PAID": InvoiceStatus.PAID,
    "OPEN": InvoiceStatus.OPEN,
    "OVERDUE": InvoiceStatus.OVERDUE,
    "PARTIAL": InvoiceStatus.PARTIAL,
    "RENEGOTIATED": InvoiceStatus.RENEGOTIATED,
    "CANCELLED": InvoiceStatus.CANCELLED,
}


class FinanceDialect:
    @classmethod
    def contract_of(cls, enrollments: Collection[EnrollmentRef]) -> ColumnElement[bool]:
        keys = [cls._contract_key(enrollment) for enrollment in enrollments]
        columns = tuple_(ContractRow.company_code, ContractRow.business_area, cls._student_number())
        return columns.in_(keys)

    @staticmethod
    def invoice_status(status: str) -> InvoiceStatus:
        return DialectLookup.find(STATUS_BY_SOURCE, status, "status")

    @staticmethod
    def _contract_key(enrollment: EnrollmentRef) -> tuple[str, str, str]:
        company = COMPANY_BY_BRAND[enrollment.brand]
        area = AREA_BY_MODALITY[enrollment.modality]
        return company, area, enrollment.student_number

    @staticmethod
    def _student_number() -> ColumnElement[str]:
        reference = func.trim(ContractRow.academic_ref)
        number = func.split_part(reference, "-", 1)
        return func.lpad(number, STUDENT_NUMBER_LENGTH, "0")

import pytest

from api.domain.brand import Brand, EnrollmentRef, Modality
from api.domain.invoice import InvoiceStatus
from api.persistence.dialect_lookup import UnknownDialectValueError
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.sag.dialect import SagDialect


def test_same_student_number_in_other_brand_is_another_enrollment() -> None:
    first = SagDialect.enrollment_ref("UniSaoPaulo_EAD", "011550")
    second = SagDialect.enrollment_ref("UniMontanhas_EAD", "011550")
    assert first != second


def test_sag_separates_modality_from_brand() -> None:
    reference = SagDialect.enrollment_ref("UniAraucaria", "090697")
    assert reference == EnrollmentRef(Brand.ARAUCARIA, Modality.IN_PERSON, "09069")


def test_finance_translates_invoice_status() -> None:
    assert FinanceDialect.invoice_status("OVERDUE") is InvoiceStatus.OVERDUE


def test_finance_raises_on_unknown_status() -> None:
    with pytest.raises(UnknownDialectValueError):
        FinanceDialect.invoice_status("WAIVED")


def test_sag_raises_on_unknown_brand() -> None:
    with pytest.raises(UnknownDialectValueError):
        SagDialect.enrollment_ref("UniDesconhecida", "011550")

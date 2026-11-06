from api.domain.finance.agreement import AgreementStatus
from api.domain.finance.contract import ContractSituation
from api.domain.finance.invoice import InvoiceKind, PaymentStatus
from api.persistence.core.dialect_lookup import DialectLookup

COMPANY_CUSTOMER = "COMPANY"
WAIVED = "True"
KIND_BY_SOURCE = {
    "TUITION": InvoiceKind.TUITION,
    "AGREEMENT_INSTALLMENT": InvoiceKind.AGREEMENT_INSTALLMENT,
    "SERVICE_FEE": InvoiceKind.SERVICE_FEE,
}
PAYMENT_STATUS_BY_SOURCE = {
    "CONFIRMED": PaymentStatus.CONFIRMED,
    "REVERSED": PaymentStatus.REVERSED,
}
SITUATION_BY_SOURCE = {
    "ACTIVE": ContractSituation.ACTIVE,
    "SUSPENDED": ContractSituation.SUSPENDED,
    "TERMINATED": ContractSituation.TERMINATED,
    "IN_COLLECTION": ContractSituation.IN_COLLECTION,
}
AGREEMENT_STATUS_BY_SOURCE = {
    "ACTIVE": AgreementStatus.ACTIVE,
    "SETTLED": AgreementStatus.SETTLED,
    "BROKEN": AgreementStatus.BROKEN,
}


class FinanceLabels:
    @staticmethod
    def invoice_kind(kind: str) -> InvoiceKind:
        return DialectLookup.find(KIND_BY_SOURCE, kind, "invoicetype")

    @staticmethod
    def payment_status(status: str) -> PaymentStatus:
        return DialectLookup.find(PAYMENT_STATUS_BY_SOURCE, status, "payment status")

    @staticmethod
    def contract_situation(status: str) -> ContractSituation:
        return DialectLookup.find(SITUATION_BY_SOURCE, status, "contract status")

    @staticmethod
    def agreement_status(status: str) -> AgreementStatus:
        return DialectLookup.find(AGREEMENT_STATUS_BY_SOURCE, status, "agreement status")

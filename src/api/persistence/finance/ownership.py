from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipRule, Public, Via
from api.persistence.finance.charge_models import (
    AgreementRow,
    DiscountRow,
    LateChargeRow,
)
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow, ProductRow

FINANCE_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    ContractRow: lambda session: FinanceDialect.contract_of(session.enrollments),
    DiscountRow: Via(ContractRow, DiscountRow.contract_id == ContractRow.id),
    InvoiceRow: Via(ContractRow, InvoiceRow.contract_id == ContractRow.id),
    PaymentRow: Via(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id),
    LateChargeRow: Via(InvoiceRow, LateChargeRow.invoice_id == InvoiceRow.id),
    AgreementRow: Via(ContractRow, AgreementRow.contract_id == ContractRow.id),
    ProductRow: Public(),
}

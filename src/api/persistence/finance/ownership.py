from sqlalchemy import select

from api.persistence.core.ownership import PUBLIC, OwnershipMap
from api.persistence.finance.charge_models import (
    AgreementRow,
    DiscountRow,
    LateChargeRow,
)
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow, ProductRow

FINANCE_OWNERSHIP: OwnershipMap = {
    ContractRow: lambda session: FinanceDialect.contract_of(session.enrollments),
    DiscountRow: lambda _: DiscountRow.contract_id.in_(select(ContractRow.id)),
    InvoiceRow: lambda _: InvoiceRow.contract_id.in_(select(ContractRow.id)),
    PaymentRow: lambda _: PaymentRow.invoice_id.in_(select(InvoiceRow.id)),
    LateChargeRow: lambda _: LateChargeRow.invoice_id.in_(select(InvoiceRow.id)),
    AgreementRow: lambda _: AgreementRow.contract_id.in_(select(ContractRow.id)),
    ProductRow: PUBLIC,
}

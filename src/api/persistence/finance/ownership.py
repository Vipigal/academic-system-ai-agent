from api.persistence.base import Base
from api.persistence.finance.charge_models import (
    AgreementRow,
    CustomerRow,
    DiscountRow,
    LateChargeRow,
)
from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow, ProductRow
from api.persistence.ownership import OwnershipRule, Public, Via

FINANCE_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    ContractRow: lambda session: ContractRow.id.in_(session.contract_ids),
    CustomerRow: Via(ContractRow, ContractRow.customer_id == CustomerRow.id),
    DiscountRow: lambda session: DiscountRow.contract_id.in_(session.contract_ids),
    InvoiceRow: lambda session: InvoiceRow.contract_id.in_(session.contract_ids),
    PaymentRow: Via(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id),
    LateChargeRow: Via(InvoiceRow, LateChargeRow.invoice_id == InvoiceRow.id),
    AgreementRow: lambda session: AgreementRow.contract_id.in_(session.contract_ids),
    ProductRow: Public(),
}

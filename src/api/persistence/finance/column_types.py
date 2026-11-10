from datetime import date
from typing import override

from sqlalchemy import Dialect

from api.domain.finance.agreement import AgreementStatus
from api.domain.finance.contract import ContractSituation
from api.domain.finance.invoice import InvoiceKind, InvoiceStatus, PaymentStatus
from api.persistence.core.column_types import IsoDate
from api.persistence.core.source_enum import SourceEnum

CONTRACT_SITUATION = SourceEnum.by_name(ContractSituation)
INVOICE_KIND = SourceEnum.by_name(InvoiceKind)
INVOICE_STATUS = SourceEnum.by_name(InvoiceStatus)
PAYMENT_STATUS = SourceEnum.by_name(PaymentStatus)
AGREEMENT_STATUS = SourceEnum.by_name(AgreementStatus)


class BlankableIsoDate(IsoDate):
    cache_ok = True

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> date | None:
        return self.from_source(value) if value else None

from datetime import date, datetime

from sqlalchemy.orm import Mapped, mapped_column

from api.domain.finance.contract import ContractSituation
from api.domain.finance.invoice import InvoiceKind, InvoiceStatus, PaymentStatus
from api.domain.shared.money import Money
from api.persistence.core.base import Base
from api.persistence.core.column_types import IsoDate, TextCents, UtcMoment
from api.persistence.core.source_enum import SourceEnum

FINANCE_SCHEMA = {"schema": "finance"}


class ContractRow(Base):
    __tablename__ = "contract"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("contractid", primary_key=True)
    company_code: Mapped[str] = mapped_column("companycode")
    business_area: Mapped[str] = mapped_column("businessarea")
    academic_ref: Mapped[str] = mapped_column("academicref")
    product_code: Mapped[str] = mapped_column("productcode")
    status: Mapped[ContractSituation] = mapped_column(SourceEnum.by_name(ContractSituation))


class InvoiceRow(Base):
    __tablename__ = "invoice"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("invoiceid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    agreement_id: Mapped[str | None] = mapped_column("agreementid")
    kind: Mapped[InvoiceKind] = mapped_column("invoicetype", SourceEnum.by_name(InvoiceKind))
    competence: Mapped[str]
    due_date: Mapped[date] = mapped_column("duedate", IsoDate())
    gross: Mapped[Money] = mapped_column("grossamountcents", TextCents())
    net: Mapped[Money] = mapped_column("netamountcents", TextCents())
    status: Mapped[InvoiceStatus] = mapped_column(SourceEnum.by_name(InvoiceStatus))
    protocol_ref: Mapped[str | None] = mapped_column("protocolref")


class PaymentRow(Base):
    __tablename__ = "payment"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("paymentid", primary_key=True)
    invoice_id: Mapped[str] = mapped_column("invoiceid")
    paid_at: Mapped[datetime] = mapped_column("paidat", UtcMoment())
    principal: Mapped[Money] = mapped_column("principalcents", TextCents())
    fine: Mapped[Money] = mapped_column("finecents", TextCents())
    interest: Mapped[Money] = mapped_column("interestcents", TextCents())
    method: Mapped[str]
    status: Mapped[PaymentStatus] = mapped_column(SourceEnum.by_name(PaymentStatus))


class ProductRow(Base):
    __tablename__ = "product"
    __table_args__ = FINANCE_SCHEMA

    code: Mapped[str] = mapped_column("productcode", primary_key=True)

from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base

FINANCE_SCHEMA = {"schema": "finance"}


class ContractRow(Base):
    __tablename__ = "contract"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("contractid", primary_key=True)
    company_code: Mapped[str] = mapped_column("companycode")
    business_area: Mapped[str] = mapped_column("businessarea")
    academic_ref: Mapped[str] = mapped_column("academicref")
    product_code: Mapped[str] = mapped_column("productcode")
    status: Mapped[str]


class InvoiceRow(Base):
    __tablename__ = "invoice"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("invoiceid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    agreement_id: Mapped[str | None] = mapped_column("agreementid")
    kind: Mapped[str] = mapped_column("invoicetype")
    competence: Mapped[str]
    due_date: Mapped[str] = mapped_column("duedate")
    gross_cents: Mapped[str] = mapped_column("grossamountcents")
    net_cents: Mapped[str] = mapped_column("netamountcents")
    status: Mapped[str]
    protocol_ref: Mapped[str | None] = mapped_column("protocolref")


class PaymentRow(Base):
    __tablename__ = "payment"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("paymentid", primary_key=True)
    invoice_id: Mapped[str] = mapped_column("invoiceid")
    paid_at: Mapped[str] = mapped_column("paidat")
    principal_cents: Mapped[str] = mapped_column("principalcents")
    fine_cents: Mapped[str] = mapped_column("finecents")
    interest_cents: Mapped[str] = mapped_column("interestcents")
    method: Mapped[str]
    status: Mapped[str]


class ProductRow(Base):
    __tablename__ = "product"
    __table_args__ = FINANCE_SCHEMA

    code: Mapped[str] = mapped_column("productcode", primary_key=True)

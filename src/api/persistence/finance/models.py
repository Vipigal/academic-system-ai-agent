from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.base import Base

FINANCE_SCHEMA = {"schema": "finance"}


class ContractRow(Base):
    __tablename__ = "contract"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("contractid", primary_key=True)
    company_code: Mapped[str] = mapped_column("companycode")
    business_area: Mapped[str] = mapped_column("businessarea")
    academic_ref: Mapped[str] = mapped_column("academicref")


class InvoiceRow(Base):
    __tablename__ = "invoice"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("invoiceid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    due_date: Mapped[str] = mapped_column("duedate")
    net_cents: Mapped[str] = mapped_column("netamountcents")
    status: Mapped[str]


class PaymentRow(Base):
    __tablename__ = "payment"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("paymentid", primary_key=True)
    invoice_id: Mapped[str] = mapped_column("invoiceid")


class ProductRow(Base):
    __tablename__ = "product"
    __table_args__ = FINANCE_SCHEMA

    code: Mapped[str] = mapped_column("productcode", primary_key=True)

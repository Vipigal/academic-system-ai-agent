from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.base import Base
from api.persistence.finance.models import FINANCE_SCHEMA


class CustomerRow(Base):
    __tablename__ = "customer"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("customerid", primary_key=True)
    customer_type: Mapped[str] = mapped_column("customertype")


class DiscountRow(Base):
    __tablename__ = "discount"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("discountid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    kind: Mapped[str] = mapped_column("discounttype")
    rate: Mapped[str]
    valid_from: Mapped[str] = mapped_column("validfrom")
    valid_to: Mapped[str | None] = mapped_column("validto")


class LateChargeRow(Base):
    __tablename__ = "late_charge"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("latechargeid", primary_key=True)
    invoice_id: Mapped[str] = mapped_column("invoiceid")
    reference_date: Mapped[str] = mapped_column("referencedate")
    fine_cents: Mapped[str] = mapped_column("finecents")
    interest_cents: Mapped[str] = mapped_column("interestcents")
    waived: Mapped[str]


class AgreementRow(Base):
    __tablename__ = "agreement"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("agreementid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    created_at: Mapped[str] = mapped_column("createdat")
    original_debt_cents: Mapped[str] = mapped_column("originaldebtcents")
    waived_cents: Mapped[str] = mapped_column("waivedcents")
    agreed_cents: Mapped[str] = mapped_column("agreedamountcents")
    status: Mapped[str]

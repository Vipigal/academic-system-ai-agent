from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column

from api.domain.finance.agreement import AgreementStatus
from api.domain.shared.money import Money
from api.persistence.core.base import Base
from api.persistence.core.column_types import (
    TRUE_FALSE,
    IsoDate,
    TextCents,
    TextDecimal,
    UtcMoment,
)
from api.persistence.core.source_enum import SourceEnum
from api.persistence.finance.column_types import BlankableIsoDate
from api.persistence.finance.models import FINANCE_SCHEMA


class DiscountRow(Base):
    __tablename__ = "discount"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("discountid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    kind: Mapped[str] = mapped_column("discounttype")
    rate: Mapped[Decimal] = mapped_column(TextDecimal())
    valid_from: Mapped[date] = mapped_column("validfrom", IsoDate())
    valid_to: Mapped[date | None] = mapped_column("validto", BlankableIsoDate())


class LateChargeRow(Base):
    __tablename__ = "late_charge"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("latechargeid", primary_key=True)
    invoice_id: Mapped[str] = mapped_column("invoiceid")
    reference_date: Mapped[date] = mapped_column("referencedate", IsoDate())
    fine: Mapped[Money] = mapped_column("finecents", TextCents())
    interest: Mapped[Money] = mapped_column("interestcents", TextCents())
    waived: Mapped[bool] = mapped_column(TRUE_FALSE)


class AgreementRow(Base):
    __tablename__ = "agreement"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("agreementid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    created_at: Mapped[datetime] = mapped_column("createdat", UtcMoment())
    original_debt: Mapped[Money] = mapped_column("originaldebtcents", TextCents())
    waived: Mapped[Money] = mapped_column("waivedcents", TextCents())
    agreed: Mapped[Money] = mapped_column("agreedamountcents", TextCents())
    status: Mapped[AgreementStatus] = mapped_column(SourceEnum.by_name(AgreementStatus))

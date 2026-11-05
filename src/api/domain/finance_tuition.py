from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise
from typing import Self

from api.domain.finance_contract import Contract, Scholarship
from api.domain.invoice import Invoice, InvoiceKind, InvoiceStatus


class TuitionChangeCause(Enum):
    PRICE_ADJUSTMENT = "price_adjustment"
    SCHOLARSHIP_ENDED = "scholarship_ended"


@dataclass(frozen=True, slots=True)
class TuitionChange:
    previous: Invoice
    current: Invoice
    ended_scholarships: tuple[Scholarship, ...]

    @classmethod
    def between(cls, contract: Contract, previous: Invoice, current: Invoice) -> Self:
        ended = tuple(
            scholarship
            for scholarship in contract.scholarships
            if scholarship.is_active_on(previous.due_date)
            and not scholarship.is_active_on(current.due_date)
        )
        return cls(previous, current, ended)

    @classmethod
    def history_of(cls, contract: Contract, invoices: Iterable[Invoice]) -> tuple[Self, ...]:
        tuition = sorted(
            (invoice for invoice in invoices if cls._is_charged_tuition(invoice, contract)),
            key=lambda invoice: (invoice.competence, invoice.id),
        )
        return tuple(
            cls.between(contract, previous, current)
            for previous, current in pairwise(tuition)
            if previous.net != current.net
        )

    @property
    def causes(self) -> tuple[TuitionChangeCause, ...]:
        price = (TuitionChangeCause.PRICE_ADJUSTMENT,) * (self.previous.gross != self.current.gross)
        ended = (TuitionChangeCause.SCHOLARSHIP_ENDED,) * bool(self.ended_scholarships)
        return price + ended

    @staticmethod
    def _is_charged_tuition(invoice: Invoice, contract: Contract) -> bool:
        return (
            invoice.contract_id == contract.id
            and invoice.kind is InvoiceKind.TUITION
            and invoice.status is not InvoiceStatus.CANCELLED
        )

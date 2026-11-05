from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

from api.domain.invoice import Invoice, Payment
from api.domain.money import Money
from api.persistence.brasilia import BrasiliaTime
from api.persistence.finance.charge_models import LateChargeRow
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.labels import WAIVED, FinanceLabels
from api.persistence.finance.models import InvoiceRow, PaymentRow


class InvoiceMapper:
    @classmethod
    def to_entities(
        cls,
        rows: Iterable[InvoiceRow],
        payments: Iterable[PaymentRow],
        late_charges: Iterable[LateChargeRow],
    ) -> Sequence[Invoice]:
        payments_by_invoice: defaultdict[str, list[Payment]] = defaultdict(list)
        for payment in payments:
            payments_by_invoice[payment.invoice_id].append(cls._payment(payment))
        last_charge = {charge.invoice_id: cls._late_charge(charge) for charge in late_charges}
        return [
            cls._invoice(
                row,
                tuple(payments_by_invoice[row.id]),
                last_charge.get(row.id, Money.from_cents(0)),
            )
            for row in rows
        ]

    @staticmethod
    def _invoice(row: InvoiceRow, payments: tuple[Payment, ...], late_charge: Money) -> Invoice:
        return Invoice(
            id=row.id,
            contract_id=row.contract_id,
            agreement_id=row.agreement_id,
            kind=FinanceLabels.invoice_kind(row.kind),
            competence=row.competence,
            due_date=date.fromisoformat(row.due_date),
            gross=Money.from_cents(int(row.gross_cents)),
            net=Money.from_cents(int(row.net_cents)),
            status=FinanceDialect.invoice_status(row.status),
            payments=payments,
            late_charge=late_charge,
        )

    @staticmethod
    def _payment(row: PaymentRow) -> Payment:
        return Payment(
            id=row.id,
            invoice_id=row.invoice_id,
            paid_at=BrasiliaTime.from_utc(row.paid_at),
            principal=Money.from_cents(int(row.principal_cents)),
            late_charge=Money.from_cents(int(row.fine_cents) + int(row.interest_cents)),
            method=row.method,
            status=FinanceLabels.payment_status(row.status),
        )

    @staticmethod
    def _late_charge(row: LateChargeRow) -> Money:
        if row.waived == WAIVED:
            return Money.from_cents(0)
        return Money.from_cents(int(row.fine_cents) + int(row.interest_cents))

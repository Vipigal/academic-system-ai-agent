from collections import defaultdict
from collections.abc import Iterable, Sequence

from api.domain.finance.invoice import Invoice, Payment
from api.domain.shared.money import Money
from api.persistence.finance.charge_models import LateChargeRow
from api.persistence.finance.models import InvoiceRow, PaymentRow

NO_LATE_CHARGE = Money(0)


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
                last_charge.get(row.id, NO_LATE_CHARGE),
            )
            for row in rows
        ]

    @staticmethod
    def _invoice(row: InvoiceRow, payments: tuple[Payment, ...], late_charge: Money) -> Invoice:
        return Invoice(
            id=row.id,
            contract_id=row.contract_id,
            agreement_id=row.agreement_id,
            kind=row.kind,
            competence=row.competence,
            due_date=row.due_date,
            gross=row.gross,
            net=row.net,
            status=row.status,
            payments=payments,
            late_charge=late_charge,
        )

    @staticmethod
    def _payment(row: PaymentRow) -> Payment:
        return Payment(
            id=row.id,
            invoice_id=row.invoice_id,
            paid_at=row.paid_at,
            principal=row.principal,
            late_charge=row.fine + row.interest,
            method=row.method,
            status=row.status,
        )

    @staticmethod
    def _late_charge(row: LateChargeRow) -> Money:
        if row.waived:
            return NO_LATE_CHARGE
        return row.fine + row.interest

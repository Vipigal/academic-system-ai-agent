from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

from api.domain.invoice import Invoice
from api.domain.money import Money
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import InvoiceRow, PaymentRow


class InvoiceMapper:
    @classmethod
    def to_entities(
        cls, rows: Iterable[InvoiceRow], payments: Iterable[PaymentRow]
    ) -> Sequence[Invoice]:
        paid_cents: defaultdict[str, int] = defaultdict(int)
        for payment in payments:
            paid_cents[payment.invoice_id] += int(payment.principal_cents)
        return [cls.to_entity(row, paid_cents[row.id]) for row in rows]

    @staticmethod
    def to_entity(row: InvoiceRow, paid_cents: int) -> Invoice:
        return Invoice(
            id=row.id,
            due_date=date.fromisoformat(row.due_date),
            net=Money.from_cents(int(row.net_cents)),
            status=FinanceDialect.invoice_status(row.status),
            paid=Money.from_cents(paid_cents),
        )

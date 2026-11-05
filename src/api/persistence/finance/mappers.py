from datetime import date

from api.domain.invoice import Invoice
from api.domain.money import Money
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import InvoiceRow


class InvoiceMapper:
    @staticmethod
    def to_entity(row: InvoiceRow) -> Invoice:
        return Invoice(
            id=row.id,
            due_date=date.fromisoformat(row.due_date),
            net=Money.from_cents(int(row.net_cents)),
            status=FinanceDialect.invoice_status(row.status),
        )

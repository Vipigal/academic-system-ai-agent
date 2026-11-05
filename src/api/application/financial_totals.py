from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from api.domain.finance_debt import DebtPosition
from api.domain.invoice import Invoice, Payment
from api.domain.money import Money


class FinanceTotals:
    @staticmethod
    def of_debt(invoices: Sequence[Invoice], reference: date) -> dict[str, Decimal | int]:
        debt = DebtPosition.of(invoices, reference)
        return {
            "debt_principal": debt.principal.reais,
            "debt_late_charge": debt.late_charge.reais,
            "debt_total": debt.total.reais,
            "overdue_invoices": len(debt.invoices),
        }

    @staticmethod
    def of_invoices(invoices: Sequence[Invoice], reference: date) -> dict[str, Decimal | int]:
        return {
            "net": Money.total(invoice.net for invoice in invoices).reais,
            "balance": Money.total(invoice.balance for invoice in invoices).reais,
            "amount_due": Money.total(invoice.amount_due(reference) for invoice in invoices).reais,
        }

    @staticmethod
    def of_payments(payments: Sequence[Payment]) -> dict[str, Decimal | int]:
        confirmed = [payment for payment in payments if payment.is_confirmed]
        reversed_payments = [payment for payment in payments if not payment.is_confirmed]
        return {
            "paid": Money.total(payment.amount for payment in confirmed).reais,
            "paid_late_charge": Money.total(payment.late_charge for payment in confirmed).reais,
            "reversed": Money.total(payment.amount for payment in reversed_payments).reais,
            "reversed_count": len(reversed_payments),
        }

from datetime import date
from decimal import Decimal

import pytest

from api.domain.invoice import Invoice, InvoiceStatus
from api.domain.money import Money

REFERENCE = date(2026, 10, 31)


def invoice_with(
    status: InvoiceStatus, due_date: date = date(2026, 10, 5), paid_cents: int = 0
) -> Invoice:
    return Invoice(
        id="7000001",
        due_date=due_date,
        net=Money.from_cents(93390),
        status=status,
        paid=Money.from_cents(paid_cents),
    )


@pytest.mark.parametrize("status", [InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL])
def test_counts_as_debt_when_already_due(status: InvoiceStatus) -> None:
    assert invoice_with(status).is_debt(REFERENCE)


@pytest.mark.parametrize("status", [InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL])
def test_does_not_count_as_debt_when_not_yet_due(status: InvoiceStatus) -> None:
    assert not invoice_with(status, due_date=date(2026, 11, 5)).is_debt(REFERENCE)


def test_does_not_count_as_debt_on_the_due_date() -> None:
    assert not invoice_with(InvoiceStatus.PARTIAL, due_date=REFERENCE).is_debt(REFERENCE)


@pytest.mark.parametrize(
    "status",
    [
        InvoiceStatus.PAID,
        InvoiceStatus.OPEN,
        InvoiceStatus.RENEGOTIATED,
        InvoiceStatus.CANCELLED,
    ],
)
def test_does_not_count_as_debt(status: InvoiceStatus) -> None:
    assert not invoice_with(status).is_debt(REFERENCE)


@pytest.mark.parametrize(
    "status",
    [InvoiceStatus.PAID, InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL],
)
def test_balance_is_net_minus_paid(status: InvoiceStatus) -> None:
    invoice = invoice_with(status, paid_cents=8101)
    assert invoice.balance == Money.from_cents(85289)


@pytest.mark.parametrize("status", [InvoiceStatus.CANCELLED, InvoiceStatus.RENEGOTIATED])
def test_balance_is_zero_when_cancelled_or_renegotiated(status: InvoiceStatus) -> None:
    assert invoice_with(status).balance == Money.from_cents(0)
    assert invoice_with(status, paid_cents=8101).balance == Money.from_cents(0)


def test_money_converts_cents_to_reais_without_float_error() -> None:
    assert Money.from_cents(19290).reais == Decimal("192.90")

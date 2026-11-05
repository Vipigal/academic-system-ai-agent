from datetime import date
from decimal import Decimal

import pytest

from api.domain.invoice import Invoice, InvoiceStatus
from api.domain.money import Money


def invoice_with(status: InvoiceStatus) -> Invoice:
    return Invoice(
        id="7000001",
        due_date=date(2026, 10, 5),
        net=Money.from_cents(93390),
        status=status,
    )


@pytest.mark.parametrize("status", [InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL])
def test_counts_as_debt(status: InvoiceStatus) -> None:
    assert invoice_with(status).is_debt()


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
    assert not invoice_with(status).is_debt()


def test_money_converts_cents_to_reais_without_float_error() -> None:
    assert Money.from_cents(19290).reais == Decimal("192.90")

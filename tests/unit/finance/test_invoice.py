from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from api.domain.finance.invoice import Invoice, InvoiceKind, InvoiceStatus, Payment, PaymentStatus
from api.domain.shared.money import Money

REFERENCE = date(2026, 10, 31)


def payment_of(cents: int, status: PaymentStatus = PaymentStatus.CONFIRMED) -> Payment:
    return Payment(
        id="9000001",
        invoice_id="7000001",
        paid_at=datetime(2026, 10, 16, tzinfo=UTC),
        principal=Money.from_cents(cents),
        late_charge=Money.from_cents(259),
        method="PIX",
        status=status,
    )


def invoice_with(
    status: InvoiceStatus,
    due_date: date = date(2026, 10, 5),
    payments: tuple[Payment, ...] = (),
    late_charge_cents: int = 0,
) -> Invoice:
    return Invoice(
        id="7000001",
        contract_id="CT00000001",
        agreement_id=None,
        kind=InvoiceKind.TUITION,
        competence="2026-10",
        due_date=due_date,
        gross=Money.from_cents(93390),
        net=Money.from_cents(93390),
        status=status,
        payments=payments,
        late_charge=Money.from_cents(late_charge_cents),
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
def test_balance_is_net_minus_confirmed_principal(status: InvoiceStatus) -> None:
    invoice = invoice_with(status, payments=(payment_of(8101),))
    assert invoice.balance == Money.from_cents(85289)


def test_reversed_payment_does_not_reduce_the_balance() -> None:
    reversed_only = (payment_of(93390, PaymentStatus.REVERSED),)
    invoice = invoice_with(InvoiceStatus.OVERDUE, payments=reversed_only)
    assert invoice.paid == Money.from_cents(0)
    assert invoice.balance == Money.from_cents(93390)


def test_reversal_followed_by_new_payment_counts_only_the_new_one() -> None:
    payments = (payment_of(8101, PaymentStatus.REVERSED), payment_of(5000))
    assert invoice_with(InvoiceStatus.PARTIAL, payments=payments).paid == Money.from_cents(5000)


@pytest.mark.parametrize("status", [InvoiceStatus.CANCELLED, InvoiceStatus.RENEGOTIATED])
def test_balance_is_zero_when_cancelled_or_renegotiated(status: InvoiceStatus) -> None:
    assert invoice_with(status).balance == Money.from_cents(0)
    assert invoice_with(status, payments=(payment_of(8101),)).balance == Money.from_cents(0)


def test_amount_due_of_a_debt_adds_the_late_charge() -> None:
    invoice = invoice_with(InvoiceStatus.OVERDUE, late_charge_cents=1000)
    assert invoice.late_charge_due(REFERENCE) == Money.from_cents(1000)
    assert invoice.amount_due(REFERENCE) == Money.from_cents(94390)


def test_late_charge_of_a_paid_invoice_is_not_due() -> None:
    paid = invoice_with(InvoiceStatus.PAID, payments=(payment_of(93390),), late_charge_cents=1000)
    assert paid.late_charge_due(REFERENCE) == Money.from_cents(0)
    assert paid.amount_due(REFERENCE) == Money.from_cents(0)


def test_days_overdue_counts_only_for_a_debt() -> None:
    assert invoice_with(InvoiceStatus.OVERDUE).days_overdue(REFERENCE) == 26
    assert invoice_with(InvoiceStatus.PAID).days_overdue(REFERENCE) == 0


@pytest.mark.parametrize("status", [InvoiceStatus.OPEN, InvoiceStatus.PARTIAL])
def test_is_upcoming_when_in_open_and_due_later(status: InvoiceStatus) -> None:
    assert invoice_with(status, due_date=date(2026, 11, 5)).is_upcoming(REFERENCE)


@pytest.mark.parametrize(
    ("status", "due_date"),
    [
        (InvoiceStatus.PAID, date(2026, 11, 5)),
        (InvoiceStatus.OPEN, date(2026, 10, 30)),
        (InvoiceStatus.PARTIAL, date(2026, 10, 5)),
    ],
)
def test_is_not_upcoming(status: InvoiceStatus, due_date: date) -> None:
    assert not invoice_with(status, due_date=due_date).is_upcoming(REFERENCE)


def test_money_converts_cents_to_reais_without_float_error() -> None:
    assert Money.from_cents(19290).reais == Decimal("192.90")


def test_money_total_adds_every_value() -> None:
    assert Money.total([Money.from_cents(10), Money.from_cents(5)]) == Money.from_cents(15)
    assert Money.total([]) == Money.from_cents(0)


@pytest.mark.parametrize("status", [InvoiceStatus.OPEN, InvoiceStatus.PARTIAL])
def test_invoice_due_on_the_reference_day_is_upcoming_and_not_a_debt(
    status: InvoiceStatus,
) -> None:
    invoice = invoice_with(status, due_date=REFERENCE)
    assert invoice.is_upcoming(REFERENCE)
    assert not invoice.is_debt(REFERENCE)

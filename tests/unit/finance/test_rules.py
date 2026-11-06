from datetime import date
from decimal import Decimal

from api.domain.finance.contract import Contract, ContractSituation, PayerType, Scholarship
from api.domain.finance.debt import DebtPosition
from api.domain.finance.invoice import Invoice, InvoiceKind, InvoiceStatus
from api.domain.finance.tuition import TuitionChange, TuitionChangeCause
from api.domain.shared.money import Money
from api.persistence.core.brasilia import BrasiliaTime

REFERENCE = date(2026, 10, 31)
CONTRACT = "CT00000001"


def tuition(
    competence: str,
    gross: int,
    net: int,
    kind: InvoiceKind = InvoiceKind.TUITION,
    status: InvoiceStatus = InvoiceStatus.PAID,
) -> Invoice:
    return Invoice(
        id=f"inv-{competence}",
        contract_id=CONTRACT,
        agreement_id=None,
        kind=kind,
        competence=competence,
        due_date=date.fromisoformat(f"{competence}-10"),
        gross=Money.from_cents(gross),
        net=Money.from_cents(net),
        status=status,
        payments=(),
        late_charge=Money.from_cents(0),
    )


def merit(valid_to: date | None) -> Scholarship:
    return Scholarship(
        id="1",
        contract_id=CONTRACT,
        kind="MERIT",
        rate=Decimal("0.15"),
        valid_from=date(2025, 1, 1),
        valid_to=valid_to,
    )


def contract_with(*scholarships: Scholarship) -> Contract:
    return Contract(
        id=CONTRACT,
        course_code="GRAD-ADS-PRE",
        situation=ContractSituation.ACTIVE,
        payer=PayerType.SELF,
        scholarships=scholarships,
    )


def test_same_value_is_no_change() -> None:
    invoices = [tuition("2026-01", 100, 100), tuition("2026-02", 100, 100)]
    assert TuitionChange.history_of(contract_with(), invoices) == ()


def test_new_gross_is_a_price_adjustment() -> None:
    invoices = [tuition("2025-12", 100, 85), tuition("2026-01", 110, 94)]
    contract = contract_with(merit(None))
    change = TuitionChange.history_of(contract, invoices)[0]
    assert change.causes == (TuitionChangeCause.PRICE_ADJUSTMENT,)
    assert change.ended_scholarships == ()


def test_scholarship_that_stops_applying_is_the_cause() -> None:
    ended = merit(date(2026, 8, 3))
    invoices = [tuition("2026-07", 100, 85), tuition("2026-08", 100, 100)]
    change = TuitionChange.history_of(contract_with(ended), invoices)[0]
    assert change.causes == (TuitionChangeCause.SCHOLARSHIP_ENDED,)
    assert change.ended_scholarships == (ended,)


def test_both_causes_can_happen_together() -> None:
    ended = merit(date(2026, 1, 3))
    invoices = [tuition("2025-12", 100, 85), tuition("2026-01", 110, 110)]
    change = TuitionChange.history_of(contract_with(ended), invoices)[0]
    assert change.causes == (
        TuitionChangeCause.PRICE_ADJUSTMENT,
        TuitionChangeCause.SCHOLARSHIP_ENDED,
    )


def test_cancelled_invoice_and_service_fee_are_not_tuition() -> None:
    invoices = [
        tuition("2026-01", 100, 100),
        tuition("2026-02", 40, 40, kind=InvoiceKind.SERVICE_FEE),
        tuition("2026-03", 200, 200, status=InvoiceStatus.CANCELLED),
        tuition("2026-04", 100, 100),
    ]
    assert TuitionChange.history_of(contract_with(), invoices) == ()


def test_scholarship_without_end_stays_active() -> None:
    assert merit(None).is_active_on(REFERENCE)
    assert not merit(date(2026, 8, 3)).is_active_on(REFERENCE)
    assert not merit(None).is_active_on(date(2024, 12, 31))


def test_debt_position_keeps_only_the_debts() -> None:
    overdue = tuition("2026-09", 100, 100, status=InvoiceStatus.OVERDUE)
    position = DebtPosition.of(
        [overdue, tuition("2026-11", 100, 100, status=InvoiceStatus.OPEN)], REFERENCE
    )
    assert position.invoices == (overdue,)
    assert position.total == Money.from_cents(100)
    assert position.max_days_overdue == 51


def test_empty_debt_position_is_zero() -> None:
    position = DebtPosition.of([], REFERENCE)
    assert position.total == Money.from_cents(0)
    assert position.max_days_overdue == 0


def test_utc_time_turns_into_brasilia_time() -> None:
    converted = BrasiliaTime.from_utc("2024-12-08 00:29:12+00:00")
    assert converted.isoformat() == "2024-12-07T21:29:12-03:00"

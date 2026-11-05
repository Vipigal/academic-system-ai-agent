import pytest

from api.application.page import PageRequest
from api.domain.invoice import InvoiceKind, InvoiceStatus
from api.persistence.database import Database
from tests.integration.finance_harness import SNAPSHOT_TOTAL, FinanceHarness
from tests.integration.sql_oracle import SqlOracle

AMOUNT_IN_2026 = (
    "SELECT sum(amountcents::int) FROM finance.payment JOIN finance.invoice USING (invoiceid) "
    "WHERE contractid = 'CT00012783' AND payment.status = :status AND paidat >= '2026'"
)
MAX_PAGE = PageRequest(limit=100)


@pytest.fixture
def harness(database: Database) -> FinanceHarness:
    return FinanceHarness(database)


@pytest.fixture
def oracle(database: Database) -> SqlOracle:
    return SqlOracle(database)


async def test_fi03_reversed_payment_shows_and_invoice_stays_due(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    tools = await harness.tools_for("3001982")
    result = await tools.list_invoices(period="2024-12")
    dumped = [item.model_dump(mode="json") for item in result.data or []]
    invoice = next(item for item in dumped if item["id"] == "7025510")
    assert await oracle.count(SNAPSHOT_TOTAL, contract="CT00011752") == 24113
    assert (invoice["status"], invoice["balance_amount_reais"], invoice["amount_due_reais"]) == (
        "overdue",
        "192.90",
        "241.13",
    )
    assert invoice["payments"] == [
        {
            "id": "9032278",
            "invoice_id": "7025510",
            "paid_at": "2024-12-07T21:29:12-03:00",
            "amount_reais": "192.90",
            "principal_reais": "192.90",
            "late_charge_reais": "0.00",
            "method": "PIX",
            "status": "reversed",
        }
    ]


async def test_fi04_payments_of_the_year_keep_reversals_apart(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    tools = await harness.tools_for("3003155")
    result = await tools.list_payments(year=2026, page=MAX_PAGE)
    paid = await oracle.count(AMOUNT_IN_2026, status="CONFIRMED")
    reversed_paid = await oracle.count(AMOUNT_IN_2026, status="REVERSED")
    assert (paid, reversed_paid) == (1633969, 161190)
    assert result.model_dump(mode="json")["totals"] == {
        "paid": "16339.69",
        "paid_late_charge": "175.69",
        "reversed": "1611.90",
        "reversed_count": 1,
    }
    assert len(result.data or []) == 11
    assert {payment.status.value for payment in result.data or []} == {"confirmed"}


async def test_fi04_year_follows_the_brasilia_date(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    tools = await harness.tools_for("3003258")
    last_year = await tools.list_payments(year=2025, page=MAX_PAGE)
    this_year = await tools.list_payments(year=2026, page=MAX_PAGE)
    utc_date = await oracle.values(
        "SELECT left(paidat, 10) FROM finance.payment WHERE paymentid = '9052923'"
    )
    assert utc_date == {"2026-01-01"}
    assert "9052923" in {payment.id for payment in last_year.data or []}
    assert "9052923" not in {payment.id for payment in this_year.data or []}


async def test_fi07_changes_come_with_their_causes(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    tools = await harness.tools_for("3003100")
    result = await tools.get_tuition_changes()
    changes = [
        item.model_dump(mode="json")
        for item in result.data or []
        if item.competence.startswith("2026")
    ]
    net_in_2026 = await oracle.values(
        "SELECT DISTINCT netamountcents FROM finance.invoice "
        "WHERE contractid = 'CT00012721' AND invoicetype = 'TUITION' AND competence >= '2026'"
    )
    assert net_in_2026 == {"101992", "119990"}
    assert [
        (item["competence"], item["previous_net_reais"], item["net_reais"], item["causes"])
        for item in changes
    ] == [
        ("2026-01", "952.76", "1019.92", ["price_adjustment"]),
        ("2026-08", "1019.92", "1199.90", ["scholarship_ended"]),
    ]
    assert (changes[0]["previous_gross_reais"], changes[0]["gross_reais"]) == ("1120.90", "1199.90")
    assert changes[1]["ended_scholarships"] == [
        {"kind": "MERIT", "rate": "0.15", "ended_on": "2026-08-03"}
    ]


async def test_fi08_agreement_counts_paid_and_remaining(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    agreement = await harness.agreement_of("3001154", "AG2026000122")
    remaining = await oracle.count(
        "SELECT sum(netamountcents::int) FROM finance.invoice "
        "WHERE agreementid = 'AG2026000122' AND status <> 'PAID'"
    )
    assert remaining == 54707
    assert (agreement["agreed_reais"], agreement["waived_reais"], agreement["status"]) == (
        "3281.87",
        "115.46",
        "active",
    )
    assert (
        agreement["installments_total"],
        agreement["installments_paid"],
        agreement["installments_remaining"],
        agreement["remaining_reais"],
    ) == (12, 10, 2, "547.07")
    assert [item["due_date"] for item in agreement["remaining_installments"]] == [
        "2026-11-22",
        "2026-12-22",
    ]


async def test_fi08_active_agreement_can_have_an_overdue_installment(
    harness: FinanceHarness,
) -> None:
    agreement = await harness.agreement_of("3001093", "AG2026000304")
    assert agreement["status"] == "active"
    assert agreement["remaining_installments"][0]["status"] == "overdue"


async def test_filters_narrow_invoices_and_totals_follow(harness: FinanceHarness) -> None:
    tools = await harness.tools_for("3003422")
    overdue = await tools.list_invoices(status=InvoiceStatus.OVERDUE)
    none_found = await tools.list_invoices(kind=InvoiceKind.SERVICE_FEE, period="1999")
    assert [invoice.id for invoice in overdue.data or []] == ["7067952"]
    assert overdue.model_dump(mode="json")["totals"]["amount_due"] == "179.65"
    assert none_found.model_dump(mode="json")["status"] == "empty"
    assert none_found.data == []


async def test_paging_invoices_reaches_the_oracle_set_with_stable_totals(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    pages = await harness.invoice_pages("3003155", limit=4)
    seen = [invoice.id for page in pages for invoice in page.data or []]
    expected = await oracle.values(
        "SELECT invoiceid FROM finance.invoice WHERE contractid = 'CT00012783'"
    )
    assert len(seen) == len(set(seen))
    assert set(seen) == expected
    assert all(page.totals == pages[0].totals for page in pages)


async def test_period_is_exact_so_a_month_prefix_does_not_bring_other_months(
    harness: FinanceHarness,
) -> None:
    tools = await harness.tools_for("3001982")
    december = await tools.list_invoices(period="2024-12")
    prefix = await tools.list_invoices(period="2024-1")
    assert december.data
    assert prefix.data == []

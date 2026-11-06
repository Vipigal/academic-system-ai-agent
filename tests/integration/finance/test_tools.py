import pytest

from api.application.agent.tools.finance import FinanceTools
from api.application.agent.tools.registry import ToolRegistry
from api.persistence.core.database import Database
from tests.integration.finance.harness import SNAPSHOT_TOTAL, FinanceHarness
from tests.integration.support.sql_oracle import SqlOracle

CUSTOMER_TYPE_BY_PAYER = {"other_person": "INDIVIDUAL", "company": "COMPANY", "self": "INDIVIDUAL"}


@pytest.fixture
def harness(database: Database) -> FinanceHarness:
    return FinanceHarness(database)


@pytest.fixture
def oracle() -> SqlOracle:
    return SqlOracle()


def test_the_five_tools_are_in_the_registry() -> None:
    assert {tool.name for tool in ToolRegistry.describe(FinanceTools)} == {
        "get_financial_summary",
        "list_invoices",
        "list_payments",
        "get_tuition_changes",
        "list_agreements",
    }


async def test_fi01_debt_is_principal_plus_last_late_charge(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    tools = await harness.tools_for("3003422")
    result = await tools.get_financial_summary()
    summary = await harness.summary_of("3003422", "CT00013016")
    assert await oracle.count(SNAPSHOT_TOTAL, contract="CT00013016") == 27705
    assert result.model_dump(mode="json")["totals"] == {
        "debt_principal": "268.85",
        "debt_late_charge": "8.20",
        "debt_total": "277.05",
        "overdue_invoices": 2,
    }
    assert summary["debt"]["reference_date"] == "2026-10-31"
    assert [
        (item["competence"], item["principal_reais"], item["late_charge_reais"])
        for item in summary["debt"]["items"]
    ] == [("2026-09", "93.92", "3.48"), ("2026-10", "174.93", "4.72")]


async def test_fi02_next_invoice_is_the_first_open_one(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    summary = await harness.summary_of("3003100", "CT00012721")
    first_open = await oracle.values(
        "SELECT min(duedate) FROM finance.invoice "
        "WHERE contractid = 'CT00012721' AND status = 'OPEN' AND duedate > '2026-10-31'"
    )
    assert first_open == {"2026-11-10"}
    assert summary["next_invoice"] == {
        "invoice_id": "7075736",
        "kind": "tuition",
        "due_date": "2026-11-10",
        "amount_reais": "1199.90",
    }


async def test_partial_invoice_due_later_is_the_next_invoice_by_its_balance(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    summary = await harness.summary_of("3003610", "CT00013240")
    balance = await oracle.count(
        "SELECT i.netamountcents::int - sum(p.principalcents::int) FROM finance.invoice i "
        "JOIN finance.payment p USING (invoiceid) "
        "WHERE i.invoiceid = '7065141' AND p.status = 'CONFIRMED' GROUP BY i.netamountcents"
    )
    assert balance == 84951
    assert summary["next_invoice"]["invoice_id"] == "7065141"
    assert summary["next_invoice"]["amount_reais"] == "849.51"
    assert summary["debt"]["overdue_invoices"] == 0


@pytest.mark.parametrize(
    ("person", "contract", "payer"),
    [
        pytest.param("3001007", "CT00010845", "other_person", id="other-person"),
        pytest.param("3003753", "CT00013379", "company", id="company"),
        pytest.param("3003422", "CT00013016", "self", id="self"),
    ],
)
async def test_fi05_payer_type_without_payer_data(
    harness: FinanceHarness, oracle: SqlOracle, person: str, contract: str, payer: str
) -> None:
    summary = await harness.summary_of(person, contract)
    payer_rows = (
        "FROM finance.customer JOIN finance.contract USING (customerid) "
        "WHERE contract.contractid = :contract"
    )
    private = await oracle.values(
        f"SELECT unnest(ARRAY[name, taxid, email, phone, customerid]) {payer_rows}",
        contract=contract,
    )
    customer_types = await oracle.values(f"SELECT customertype {payer_rows}", contract=contract)
    assert customer_types == {CUSTOMER_TYPE_BY_PAYER[payer]}
    assert summary["payer"] == payer
    assert private
    assert not [value for value in private if value in str(summary)]


async def test_fi06_full_scholarship_explains_the_lack_of_invoices(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    summary = await harness.summary_of("3003258", "CT00013587")
    invoices = await oracle.count(
        "SELECT count(*) FROM finance.invoice WHERE contractid = 'CT00013587'"
    )
    assert invoices == 0
    assert summary["tuition_invoices"] == 0
    assert summary["next_invoice"] is None
    assert summary["scholarships"] == [
        {
            "kind": "PROUNI_100",
            "rate": "1.0",
            "valid_from": "2026-08-01",
            "valid_to": None,
            "is_active": True,
        }
    ]


async def test_fi09_collection_shows_no_internal_stage(
    harness: FinanceHarness, oracle: SqlOracle
) -> None:
    summary = await harness.summary_of("3001096", "CT00010916")
    stages = await oracle.values(
        "SELECT collectionstage FROM finance.receivable_snapshot UNION "
        "SELECT agingbucket FROM finance.receivable_snapshot"
    )
    debt = summary["debt"]
    assert summary["situation"] == "in_collection"
    assert (debt["overdue_invoices"], debt["total_reais"], debt["max_days_overdue"]) == (
        24,
        "44251.08",
        720,
    )
    assert await oracle.count(SNAPSHOT_TOTAL, contract="CT00010916") == 4425108
    assert "CREDIT_BUREAU" in stages
    assert not [stage for stage in stages if stage in str(summary)]


async def test_cr05_suspended_contract_without_debt(harness: FinanceHarness) -> None:
    summary = await harness.summary_of("3001432", "CT00012266")
    assert summary["situation"] == "suspended"
    assert summary["debt"]["total_reais"] == "0.00"


async def test_cr06_terminated_contract_keeps_agreement_installments(
    harness: FinanceHarness,
) -> None:
    summary = await harness.summary_of("3002891", "CT00012543")
    agreement = await harness.agreement_of("3002891", "AG2026000321")
    upcoming = summary["next_invoice"]
    assert summary["situation"] == "terminated"
    assert (upcoming["kind"], upcoming["amount_reais"], upcoming["due_date"]) == (
        "agreement_installment",
        "517.41",
        "2026-11-28",
    )
    assert (agreement["installments_remaining"], agreement["remaining_reais"]) == (5, "2587.09")


@pytest.mark.parametrize(
    ("person", "contract", "total"),
    [
        pytest.param("3000755", "CT00010601", "34.42", id="cr07-old-enrollment"),
        pytest.param("3000210", "CT00010681", "51.91", id="cr03-debt-with-diploma"),
    ],
)
async def test_debt_of_a_previous_contract_is_visible(
    harness: FinanceHarness, person: str, contract: str, total: str
) -> None:
    summary = await harness.summary_of(person, contract)
    assert summary["debt"]["total_reais"] == total
    assert summary["debt"]["items"][0]["kind"] == "service_fee"


async def test_unknown_person_gets_only_empty_results(harness: FinanceHarness) -> None:
    tools = await harness.tools_for("0000000")
    results = (
        await tools.get_financial_summary(),
        await tools.list_payments(),
        await tools.list_agreements(),
        await tools.get_tuition_changes(),
    )
    assert {result.model_dump(mode="json")["status"] for result in results} == {"empty"}

import asyncio
from datetime import date
from decimal import Decimal

from api.application.finance.dto.invoice import InvoiceDto
from api.application.finance.service import FinancialService
from api.domain.finance.invoice import InvoiceKind, InvoiceStatus
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import SLOW, SWEEP, all_pages, tools_factory

PERSON_WITH_OVERDUE_INVOICE = "3001982"
OTHER_PERSON = "3000071"
OVERDUE_INVOICE = "7025510"
OWN_CONTRACT = "CT00011752"
PARTIAL_INVOICE = "7067951"
PARTIAL_PERSON = "3003422"
NOT_YET_DUE_PERSON = "3003610"
NOT_YET_DUE_CONTRACT = "CT00013240"
SNAPSHOT_CONTRACTS = (
    "SELECT count(DISTINCT contractid) FROM finance.receivable_snapshot "
    "WHERE snapshotdate = '2026-10-31'"
)


async def service_for(database: Database, person_id: str) -> FinancialService:
    return await tools_factory(database).of_person(person_id, FinancialService)


async def all_invoices_of(service: FinancialService) -> list[InvoiceDto]:
    return await all_pages(lambda page: service.list_invoices(page=page))


async def debts_of(service: FinancialService) -> list[InvoiceDto]:
    return (await service.list_debts()).data or []


async def test_lists_the_invoices_of_the_person(database: Database) -> None:
    service = await service_for(database, PERSON_WITH_OVERDUE_INVOICE)
    invoices = await all_invoices_of(service)
    expected = await SqlOracle().values(
        "SELECT invoiceid FROM finance.invoice WHERE contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {invoice.id for invoice in invoices} == expected


async def test_debts_exclude_open_and_renegotiated_invoices(database: Database) -> None:
    service = await service_for(database, PERSON_WITH_OVERDUE_INVOICE)
    debts = await debts_of(service)
    expected = await SqlOracle().values(
        "SELECT invoiceid FROM finance.invoice "
        "WHERE contractid = :contract AND status IN ('OVERDUE', 'PARTIAL') "
        "AND duedate < '2026-10-31'",
        contract=OWN_CONTRACT,
    )
    assert {debt.id for debt in debts} == expected


async def test_dto_uses_canonical_values(database: Database) -> None:
    service = await service_for(database, PERSON_WITH_OVERDUE_INVOICE)
    debts = await debts_of(service)
    overdue = next(debt for debt in debts if debt.id == OVERDUE_INVOICE)
    assert overdue.model_copy(update={"payments": ()}) == InvoiceDto(
        id=OVERDUE_INVOICE,
        contract_id=OWN_CONTRACT,
        kind=InvoiceKind.TUITION,
        competence="2024-12",
        due_date=date(2024, 12, 10),
        net_amount_reais=Decimal("192.90"),
        balance_amount_reais=Decimal("192.90"),
        late_charge_reais=Decimal("48.23"),
        amount_due_reais=Decimal("241.13"),
        status=InvoiceStatus.OVERDUE,
        is_debt=True,
        payments=(),
    )


async def test_other_person_never_sees_the_invoice(database: Database) -> None:
    service = await service_for(database, OTHER_PERSON)
    invoices = await all_invoices_of(service)
    assert invoices
    assert OVERDUE_INVOICE not in {invoice.id for invoice in invoices}


async def invoices_seen_by_each_person(services: list[FinancialService]) -> list[str]:
    per_person = await asyncio.gather(*(all_invoices_of(service) for service in services))
    return [invoice.id for invoices in per_person for invoice in invoices]


@SWEEP
@SLOW
async def test_every_invoice_belongs_to_exactly_one_person(
    financial_services: list[FinancialService],
) -> None:
    seen = await invoices_seen_by_each_person(financial_services)
    all_invoices = await SqlOracle().values("SELECT invoiceid FROM finance.invoice")
    assert len(seen) == len(set(seen))
    assert set(seen) == all_invoices


def test_dto_exposes_only_the_allowed_fields() -> None:
    assert set(InvoiceDto.model_fields) == {
        "id",
        "contract_id",
        "kind",
        "competence",
        "due_date",
        "net_amount_reais",
        "balance_amount_reais",
        "late_charge_reais",
        "amount_due_reais",
        "status",
        "is_debt",
        "payments",
    }


async def test_partial_invoice_balance_is_net_minus_confirmed_payments(database: Database) -> None:
    service = await service_for(database, PARTIAL_PERSON)
    invoices = await all_invoices_of(service)
    partial = next(invoice for invoice in invoices if invoice.id == PARTIAL_INVOICE)
    assert partial.net_amount_reais == Decimal("174.93")
    assert partial.balance_amount_reais == Decimal("93.92")
    assert partial.is_debt


async def oracle_rows(sql: str) -> set[str]:
    return await SqlOracle().values(sql)


async def test_partial_invoice_not_yet_due_is_not_debt(database: Database) -> None:
    not_yet_due = await SqlOracle().values(
        "SELECT invoiceid FROM finance.invoice "
        "WHERE contractid = :contract AND status = 'PARTIAL' AND duedate >= '2026-10-31'",
        contract=NOT_YET_DUE_CONTRACT,
    )
    service = await service_for(database, NOT_YET_DUE_PERSON)
    invoices = await all_invoices_of(service)
    debts = await debts_of(service)
    assert not_yet_due
    assert not_yet_due <= {invoice.id for invoice in invoices}
    assert not not_yet_due & {debt.id for debt in debts}


async def debts_of_everyone(services: list[FinancialService]) -> list[InvoiceDto]:
    per_person = await asyncio.gather(*(debts_of(service) for service in services))
    return [debt for debts in per_person for debt in debts]


async def snapshot_by_contract() -> dict[str, tuple[int, int]]:
    rows = await oracle_rows(
        "SELECT contractid || ':' || principalcents || ':' || overdueinvoices "
        "FROM finance.receivable_snapshot WHERE snapshotdate = '2026-10-31'",
    )
    parts = [row.split(":") for row in rows]
    return {contract: (int(principal), int(count)) for contract, principal, count in parts}


async def debt_cents_by_contract(services: list[FinancialService]) -> list[tuple[str, int]]:
    debts = await debts_of_everyone(services)
    return [(debt.contract_id, int(debt.balance_amount_reais * 100)) for debt in debts]


def principal_and_count(debts: list[tuple[str, int]]) -> dict[str, tuple[int, int]]:
    totals: dict[str, tuple[int, int]] = {}
    for contract, cents in debts:
        principal, count = totals.get(contract, (0, 0))
        totals[contract] = (principal + cents, count + 1)
    return totals


@SWEEP
@SLOW
async def test_debt_matches_the_receivable_snapshot_contract_by_contract(
    financial_services: list[FinancialService],
) -> None:
    expected = await snapshot_by_contract()
    assert len(expected) == await SqlOracle().count(SNAPSHOT_CONTRACTS)
    assert principal_and_count(await debt_cents_by_contract(financial_services)) == expected


async def test_invoices_come_in_a_total_order(database: Database) -> None:
    session = await StudentSessionRepository(database).load(PERSON_WITH_OVERDUE_INVOICE)
    adapter = RepositoryAdapter(database, session)
    invoices = await SqlFinanceRepository(adapter).list_invoices()
    assert invoices == sorted(invoices, key=lambda invoice: (invoice.due_date, invoice.id))

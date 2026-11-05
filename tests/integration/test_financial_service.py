from datetime import date
from decimal import Decimal

from api.application.dto.invoice_dto import InvoiceDto
from api.application.financial_service import FinancialService
from api.domain.invoice import InvoiceStatus
from api.persistence.database import Database
from api.persistence.finance.repositories import FinanceInvoiceRepository
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.student_session_repository import StudentSessionRepository
from tests.integration.sql_oracle import SqlOracle

PERSON_WITH_OVERDUE_INVOICE = "3001982"
OTHER_PERSON = "3000071"
OVERDUE_INVOICE = "7025510"
OWN_CONTRACT = "CT00011752"
REFERENCE = date(2026, 10, 31)
PARTIAL_INVOICE = "7067951"
PARTIAL_PERSON = "3003422"
NOT_YET_DUE_PERSON = "3003610"
NOT_YET_DUE_CONTRACT = "CT00013240"


class FixedClock:
    def __init__(self, today: date) -> None:
        self._today = today

    def today(self) -> date:
        return self._today


async def service_for(database: Database, person_id: str) -> FinancialService:
    session = await StudentSessionRepository(database.db_session_factory).load(person_id)
    adapter = RepositoryAdapter(database.db_session_factory, session)
    return FinancialService(FinanceInvoiceRepository(adapter), FixedClock(REFERENCE))


async def test_lists_the_invoices_of_the_person(database: Database) -> None:
    service = await service_for(database, PERSON_WITH_OVERDUE_INVOICE)
    invoices = await service.list_invoices()
    expected = await SqlOracle(database).values(
        "SELECT invoiceid FROM finance.invoice WHERE contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {invoice.id for invoice in invoices} == expected


async def test_debts_exclude_open_and_renegotiated_invoices(database: Database) -> None:
    service = await service_for(database, PERSON_WITH_OVERDUE_INVOICE)
    debts = await service.list_debts()
    expected = await SqlOracle(database).values(
        "SELECT invoiceid FROM finance.invoice "
        "WHERE contractid = :contract AND status IN ('OVERDUE', 'PARTIAL') "
        "AND duedate < '2026-10-31'",
        contract=OWN_CONTRACT,
    )
    assert {debt.id for debt in debts} == expected


async def test_dto_uses_canonical_values(database: Database) -> None:
    service = await service_for(database, PERSON_WITH_OVERDUE_INVOICE)
    debts = await service.list_debts()
    overdue = next(debt for debt in debts if debt.id == OVERDUE_INVOICE)
    assert overdue == InvoiceDto(
        id=OVERDUE_INVOICE,
        due_date=date(2024, 12, 10),
        net_amount_reais=Decimal("192.90"),
        balance_amount_reais=Decimal("192.90"),
        status=InvoiceStatus.OVERDUE,
        is_debt=True,
    )


async def test_other_person_never_sees_the_invoice(database: Database) -> None:
    service = await service_for(database, OTHER_PERSON)
    invoices = await service.list_invoices()
    assert invoices
    assert OVERDUE_INVOICE not in {invoice.id for invoice in invoices}


async def invoices_seen_by_each_person(database: Database) -> list[str]:
    one_id_per_person = await SqlOracle(database).values(
        "SELECT min(person_id) FROM sag.person GROUP BY cpf",
    )
    services = [await service_for(database, person_id) for person_id in one_id_per_person]
    per_person = [await service.list_invoices() for service in services]
    return [invoice.id for invoices in per_person for invoice in invoices]


async def test_every_invoice_belongs_to_exactly_one_person(database: Database) -> None:
    seen = await invoices_seen_by_each_person(database)
    all_invoices = await SqlOracle(database).values("SELECT invoiceid FROM finance.invoice")
    assert len(seen) == len(set(seen))
    assert set(seen) == all_invoices


def test_dto_exposes_only_the_allowed_fields() -> None:
    assert set(InvoiceDto.model_fields) == {
        "id",
        "due_date",
        "net_amount_reais",
        "balance_amount_reais",
        "status",
        "is_debt",
    }


async def test_partial_invoice_balance_is_net_minus_confirmed_payments(database: Database) -> None:
    service = await service_for(database, PARTIAL_PERSON)
    invoices = await service.list_invoices()
    partial = next(invoice for invoice in invoices if invoice.id == PARTIAL_INVOICE)
    assert partial.net_amount_reais == Decimal("174.93")
    assert partial.balance_amount_reais == Decimal("93.92")
    assert partial.is_debt


async def oracle_rows(database: Database, sql: str) -> set[str]:
    return await SqlOracle(database).values(sql)


async def test_partial_invoice_not_yet_due_is_not_debt(database: Database) -> None:
    not_yet_due = await SqlOracle(database).values(
        "SELECT invoiceid FROM finance.invoice "
        "WHERE contractid = :contract AND status = 'PARTIAL' AND duedate >= '2026-10-31'",
        contract=NOT_YET_DUE_CONTRACT,
    )
    service = await service_for(database, NOT_YET_DUE_PERSON)
    invoices = await service.list_invoices()
    debts = await service.list_debts()
    assert not_yet_due
    assert not_yet_due <= {invoice.id for invoice in invoices}
    assert not not_yet_due & {debt.id for debt in debts}


async def debts_of_everyone(database: Database) -> list[InvoiceDto]:
    one_id_per_person = await oracle_rows(
        database, "SELECT min(person_id) FROM sag.person GROUP BY cpf"
    )
    services = [await service_for(database, person_id) for person_id in one_id_per_person]
    return [debt for service in services for debt in await service.list_debts()]


async def snapshot_by_contract(database: Database) -> dict[str, tuple[int, int]]:
    rows = await oracle_rows(
        database,
        "SELECT contractid || ':' || principalcents || ':' || overdueinvoices "
        "FROM finance.receivable_snapshot WHERE snapshotdate = '2026-10-31'",
    )
    parts = [row.split(":") for row in rows]
    return {contract: (int(principal), int(count)) for contract, principal, count in parts}


async def debt_cents_by_contract(database: Database) -> list[tuple[str, int]]:
    pairs = await oracle_rows(
        database, "SELECT invoiceid || ':' || contractid FROM finance.invoice"
    )
    contract_of_invoice = dict(pair.split(":") for pair in pairs)
    debts = await debts_of_everyone(database)
    return [(contract_of_invoice[debt.id], int(debt.balance_amount_reais * 100)) for debt in debts]


def principal_and_count(debts: list[tuple[str, int]]) -> dict[str, tuple[int, int]]:
    totals: dict[str, tuple[int, int]] = {}
    for contract, cents in debts:
        principal, count = totals.get(contract, (0, 0))
        totals[contract] = (principal + cents, count + 1)
    return totals


async def test_debt_matches_the_receivable_snapshot_contract_by_contract(
    database: Database,
) -> None:
    expected = await snapshot_by_contract(database)
    assert len(expected) == 273
    assert principal_and_count(await debt_cents_by_contract(database)) == expected


async def test_invoices_come_in_a_total_order(database: Database) -> None:
    session = await StudentSessionRepository(database.db_session_factory).load(
        PERSON_WITH_OVERDUE_INVOICE
    )
    repository = FinanceInvoiceRepository(RepositoryAdapter(database.db_session_factory, session))
    invoices = await repository.list_all()
    assert invoices == sorted(invoices, key=lambda invoice: (invoice.due_date, invoice.id))

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


async def service_for(database: Database, person_id: str) -> FinancialService:
    session = await StudentSessionRepository(database.db_session_factory).load(person_id)
    adapter = RepositoryAdapter(database.db_session_factory, session)
    return FinancialService(FinanceInvoiceRepository(adapter))


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
        "WHERE contractid = :contract AND status IN ('OVERDUE', 'PARTIAL')",
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
        "status",
        "is_debt",
    }

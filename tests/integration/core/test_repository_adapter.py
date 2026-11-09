import pytest
from sqlalchemy import or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow, ProductRow
from api.persistence.identity.payer_queries import PayerQueries
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.support.sql_oracle import SqlOracle

OWNER = "3001982"
OWN_CONTRACT = "CT00011752"
EMPTY_SESSION = StudentSession(person_ids=frozenset(), cpf="", enrollment_keys=frozenset())
OF_CONTRACT = InvoiceRow.contract_id == ContractRow.id
OWN_INVOICES = select(InvoiceRow).join(ContractRow, OF_CONTRACT)


SECRETARY_SCHEMA = {"schema": "secretary"}


class UndeclaredBase(DeclarativeBase):
    pass


class UndeclaredRow(UndeclaredBase):
    __tablename__ = "analyst"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("analyst_id", primary_key=True)


@pytest.fixture
async def session(database: Database) -> StudentSession:
    return await StudentSessionRepository(database.db_session_factory).load(OWNER)


@pytest.fixture
def adapter(database: Database, session: StudentSession) -> RepositoryAdapter:
    return RepositoryAdapter(database.db_session_factory, session)


def adapter_for(database: Database, session: StudentSession) -> RepositoryAdapter:
    return RepositoryAdapter(database.db_session_factory, session)


async def test_restricts_rows_to_the_session_contracts(adapter: RepositoryAdapter) -> None:
    rows = await adapter.fetch(OWN_INVOICES)
    expected = await SqlOracle().values(
        "SELECT invoiceid FROM finance.invoice WHERE contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {row.id for row in rows} == expected
    assert "7025510" in expected


async def test_empty_session_sees_nothing(database: Database) -> None:
    assert await adapter_for(database, EMPTY_SESSION).fetch(OWN_INVOICES) == []


async def test_or_in_the_query_cannot_widen_the_result(adapter: RepositoryAdapter) -> None:
    statement = OWN_INVOICES.where(or_(InvoiceRow.status == "PAID", InvoiceRow.status == "OVERDUE"))
    rows = await adapter.fetch(statement)
    assert rows
    assert {row.contract_id for row in rows} == {OWN_CONTRACT}


async def test_join_with_parent_applies_the_parent_ownership(adapter: RepositoryAdapter) -> None:
    statement = (
        select(PaymentRow)
        .join(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id)
        .join(ContractRow, OF_CONTRACT)
    )
    rows = await adapter.fetch(statement)
    expected = await SqlOracle().values(
        "SELECT p.paymentid FROM finance.payment p "
        "JOIN finance.invoice i ON p.invoiceid = i.invoiceid WHERE i.contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {row.id for row in rows} == expected


async def test_public_table_is_not_filtered(database: Database) -> None:
    rows = await adapter_for(database, EMPTY_SESSION).fetch(select(ProductRow))
    total = await SqlOracle().count("SELECT count(*) FROM finance.product")
    assert len(rows) == total


async def test_rejects_table_without_declaration(adapter: RepositoryAdapter) -> None:
    with pytest.raises(OwnershipError):
        await adapter.fetch(select(UndeclaredRow))


async def test_wrong_join_condition_cannot_bring_rows_of_other_people(
    adapter: RepositoryAdapter,
) -> None:
    statement = (
        select(PaymentRow)
        .join(InvoiceRow, PaymentRow.id == PaymentRow.id)
        .join(ContractRow, ContractRow.id == ContractRow.id)
    )
    rows = await adapter.fetch(statement)
    own_payments = await SqlOracle().values(
        "SELECT p.paymentid FROM finance.payment p "
        "JOIN finance.invoice i ON p.invoiceid = i.invoiceid WHERE i.contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {row.id for row in rows} == own_payments


async def test_payer_query_keeps_the_ownership_of_the_root(
    adapter: RepositoryAdapter, session: StudentSession
) -> None:
    rows = await adapter.fetch_rows(PayerQueries.contracts_with_payer(session.cpf))
    assert [contract.id for contract, _ in rows] == [OWN_CONTRACT]


async def test_payer_query_of_an_empty_session_sees_nothing(database: Database) -> None:
    payer_query = PayerQueries.contracts_with_payer(EMPTY_SESSION.cpf)
    assert await adapter_for(database, EMPTY_SESSION).fetch_rows(payer_query) == []

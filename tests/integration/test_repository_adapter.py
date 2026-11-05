from dataclasses import replace

import pytest
from sqlalchemy import or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.finance.models import InvoiceRow, PaymentRow, ProductRow
from api.persistence.ownership import OwnershipError
from api.persistence.repository_adapter import RepositoryAdapter
from tests.integration.sql_oracle import SqlOracle

OWN_CONTRACT = "CT00011752"
SESSION = StudentSession(
    person_ids=frozenset({"3001982"}),
    cpf="",
    enrollment_keys=frozenset(),
    brands=frozenset(),
    contract_ids=frozenset({OWN_CONTRACT}),
    self_paid_contract_ids=frozenset(),
    company_paid_contract_ids=frozenset(),
    lms_user_ids=frozenset(),
    protocol_ids=frozenset(),
)
EMPTY_SESSION = replace(SESSION, person_ids=frozenset(), contract_ids=frozenset())


SECRETARY_SCHEMA = {"schema": "secretary"}


class UndeclaredBase(DeclarativeBase):
    pass


class UndeclaredRow(UndeclaredBase):
    __tablename__ = "analyst"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("analyst_id", primary_key=True)


def adapter_for(database: Database, session: StudentSession = SESSION) -> RepositoryAdapter:
    return RepositoryAdapter(database.db_session_factory, session)


async def test_restricts_rows_to_the_session_contracts(database: Database) -> None:
    rows = await adapter_for(database).fetch(select(InvoiceRow))
    expected = await SqlOracle(database).values(
        "SELECT invoiceid FROM finance.invoice WHERE contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {row.id for row in rows} == expected
    assert "7025510" in expected


async def test_empty_session_sees_nothing(database: Database) -> None:
    assert await adapter_for(database, EMPTY_SESSION).fetch(select(InvoiceRow)) == []


async def test_or_in_the_query_cannot_widen_the_result(database: Database) -> None:
    statement = select(InvoiceRow).where(
        or_(InvoiceRow.status == "PAID", InvoiceRow.status == "OVERDUE")
    )
    rows = await adapter_for(database).fetch(statement)
    assert rows
    assert {row.contract_id for row in rows} == {OWN_CONTRACT}


async def test_table_without_owner_column_requires_join_with_parent(database: Database) -> None:
    with pytest.raises(OwnershipError):
        await adapter_for(database).fetch(select(PaymentRow))


async def test_join_with_parent_applies_the_parent_ownership(database: Database) -> None:
    statement = select(PaymentRow).join(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id)
    rows = await adapter_for(database).fetch(statement)
    expected = await SqlOracle(database).values(
        "SELECT p.paymentid FROM finance.payment p "
        "JOIN finance.invoice i ON p.invoiceid = i.invoiceid WHERE i.contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {row.id for row in rows} == expected


async def test_public_table_is_not_filtered(database: Database) -> None:
    rows = await adapter_for(database, EMPTY_SESSION).fetch(select(ProductRow))
    total = await SqlOracle(database).count("SELECT count(*) FROM finance.product")
    assert len(rows) == total


async def test_rejects_table_without_declaration(database: Database) -> None:
    with pytest.raises(OwnershipError):
        await adapter_for(database).fetch(select(UndeclaredRow))


async def test_wrong_join_condition_cannot_bring_rows_of_other_people(database: Database) -> None:
    statement = select(PaymentRow).join(InvoiceRow, PaymentRow.id == PaymentRow.id)
    rows = await adapter_for(database).fetch(statement)
    own_payments = await SqlOracle(database).values(
        "SELECT p.paymentid FROM finance.payment p "
        "JOIN finance.invoice i ON p.invoiceid = i.invoiceid WHERE i.contractid = :contract",
        contract=OWN_CONTRACT,
    )
    assert {row.id for row in rows} == own_payments


async def test_adapter_runs_the_guard_before_reaching_the_database(database: Database) -> None:
    with pytest.raises(OwnershipError):
        await adapter_for(database).fetch(select(InvoiceRow).suffix_with("OR true"))

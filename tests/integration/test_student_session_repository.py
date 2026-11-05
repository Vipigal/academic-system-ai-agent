import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.invoice import InvoiceStatus
from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.sag.dialect import SagDialect
from api.persistence.student_session_repository import StudentSessionRepository
from tests.integration.sql_oracle import SqlOracle


def repository_for(database: Database) -> StudentSessionRepository:
    return StudentSessionRepository(database.db_session_factory)


async def test_loads_the_contract_of_the_person(database: Database) -> None:
    session = await repository_for(database).load("3001982")
    assert session.person_ids == {"3001982"}
    assert session.contract_ids == {"CT00011752"}


async def test_person_with_two_ids_gets_the_same_session_from_either(database: Database) -> None:
    repository = repository_for(database)
    first = await repository.load("3000071")
    second = await repository.load("3017324")
    assert first.person_ids == {"3000071", "3017324"}
    assert first == second


async def test_unknown_person_gets_an_empty_session(database: Database) -> None:
    session = await repository_for(database).load("does-not-exist")
    assert not session.person_ids
    assert not session.enrollment_keys
    assert not session.brands
    assert not session.contract_ids
    assert not session.lms_user_ids


async def test_unknown_person_owns_no_protocol_nor_paid_contract(database: Database) -> None:
    session = await repository_for(database).load("does-not-exist")
    assert not session.protocol_ids
    assert not session.self_paid_contract_ids


async def test_the_session_never_shows_the_cpf(database: Database) -> None:
    session = await repository_for(database).load("3001982")
    assert session.cpf.isdigit()
    assert len(session.cpf) == 11
    assert session.cpf not in repr(session)


async def test_enrollment_keys_keep_the_spelling_of_the_source(database: Database) -> None:
    session = await repository_for(database).load("3000071")
    expected = await SqlOracle(database).values(
        "SELECT brand || ':' || student_id FROM sag.enrollment "
        "WHERE person_id IN ('3000071', '3017324')",
    )
    assert {":".join(key) for key in session.enrollment_keys} == expected
    assert session.brands == {
        SagDialect.enrollment_ref(*key).brand for key in session.enrollment_keys
    }


async def test_every_contract_belongs_to_exactly_one_person(
    database: Database, everyone: list[StudentSession]
) -> None:
    owned = [contract for session in everyone for contract in session.contract_ids]
    all_contracts = await SqlOracle(database).values("SELECT contractid FROM finance.contract")
    assert len(owned) == len(set(owned))
    assert set(owned) == all_contracts


async def test_every_invoice_status_in_the_database_has_translation(database: Database) -> None:
    statuses = await SqlOracle(database).values("SELECT DISTINCT status FROM finance.invoice")
    translated = {FinanceDialect.invoice_status(status) for status in statuses}
    assert translated == set(InvoiceStatus)


async def test_person_without_cpf_gets_an_empty_session(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_cpf(_db: AsyncSession, _person_id: str) -> str:
        return ""

    monkeypatch.setattr(StudentSessionRepository, "_cpf_of", staticmethod(no_cpf))
    session = await StudentSessionRepository(database.db_session_factory).load("3001982")
    assert not session.person_ids
    assert not session.contract_ids
    assert not session.protocol_ids

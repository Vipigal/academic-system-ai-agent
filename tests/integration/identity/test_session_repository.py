import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from api.bootstrap.settings import Settings
from api.domain.finance.invoice import InvoiceStatus
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.finance.column_types import INVOICE_STATUS
from api.persistence.identity.student_session_repository import StudentSessionRepository
from api.persistence.sag.dialect import SagDialect
from tests.integration.support.owned import Owned, owned_by
from tests.integration.support.sql_oracle import SqlOracle

MAX_SESSION_QUERIES = 3


def repository_for(database: Database) -> StudentSessionRepository:
    return StudentSessionRepository(database)


async def owned_of(database: Database, person_id: str) -> Owned:
    return await owned_by(database, await repository_for(database).load(person_id))


async def test_loads_the_contract_of_the_person(database: Database) -> None:
    owned = await owned_of(database, "3001982")
    assert owned.person_ids == {"3001982"}
    assert owned.contract_ids == {"CT00011752"}


async def test_person_with_two_ids_gets_the_same_session_from_either(database: Database) -> None:
    repository = repository_for(database)
    first = await repository.load("3000071")
    second = await repository.load("3017324")
    assert first.person_ids == {"3000071", "3017324"}
    assert first == second


async def test_unknown_person_gets_an_empty_session(database: Database) -> None:
    owned = await owned_of(database, "does-not-exist")
    assert not owned.person_ids
    assert not owned.enrollment_keys
    assert not owned.session.brands
    assert not owned.contract_ids
    assert not owned.lms_user_ids


async def test_unknown_person_owns_no_protocol_nor_paid_contract(database: Database) -> None:
    owned = await owned_of(database, "does-not-exist")
    assert not owned.protocol_ids
    assert not owned.self_paid_contract_ids


async def test_the_session_never_shows_the_cpf(database: Database) -> None:
    session = await repository_for(database).load("3001982")
    assert session.cpf.isdigit()
    assert len(session.cpf) == 11
    assert session.cpf not in repr(session)


async def test_enrollment_keys_keep_the_spelling_of_the_source(database: Database) -> None:
    session = await repository_for(database).load("3000071")
    expected = await SqlOracle().values(
        "SELECT brand || ':' || student_id FROM sag.enrollment "
        "WHERE person_id IN ('3000071', '3017324')",
    )
    assert {f"{key.source_brand}:{key.student_id}" for key in session.enrollment_keys} == expected
    assert session.brands == {
        SagDialect.enrollment_ref(key.source_brand, key.student_id).brand
        for key in session.enrollment_keys
    }


async def test_loading_the_session_takes_at_most_three_queries() -> None:
    connected = Database(Settings.from_environment().database_url.get_secret_value())
    repository = StudentSessionRepository(connected)
    engine = connected.db_session_factory.kw["bind"]
    statements: list[object] = []

    def record(*arguments: object) -> None:
        statements.append(arguments[2])

    await repository.load("3000071")
    event.listen(engine.sync_engine, "before_cursor_execute", record)
    session = await repository.load("3000071")
    await connected.dispose()
    assert session.enrollment_keys
    assert 1 <= len(statements) <= MAX_SESSION_QUERIES


@pytest.mark.sweep
async def test_every_contract_belongs_to_exactly_one_person(owned_by_everyone: list[Owned]) -> None:
    owned = [contract for person in owned_by_everyone for contract in person.contract_ids]
    all_contracts = await SqlOracle().values("SELECT contractid FROM finance.contract")
    assert len(owned) == len(set(owned))
    assert set(owned) == all_contracts


async def test_every_invoice_status_in_the_database_has_translation() -> None:
    statuses = await SqlOracle().values("SELECT DISTINCT status FROM finance.invoice")
    translated = {INVOICE_STATUS.from_source(status) for status in statuses}
    assert translated == set(InvoiceStatus)


async def test_person_without_cpf_gets_an_empty_session(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_cpf(_db: AsyncSession, _person_id: str) -> str:
        return ""

    monkeypatch.setattr(StudentSessionRepository, "_cpf_of", staticmethod(no_cpf))
    session: StudentSession = await repository_for(database).load("3001982")
    owned = await owned_by(database, session)
    assert not owned.person_ids
    assert not owned.contract_ids
    assert not owned.protocol_ids

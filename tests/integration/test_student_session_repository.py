from api.domain.invoice import InvoiceStatus
from api.persistence.database import Database
from api.persistence.finance.dialect import FinanceDialect
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
    assert not session.contract_ids


async def contracts_owned_by_each_person(database: Database) -> list[str]:
    one_id_per_person = await SqlOracle(database).values(
        "SELECT min(person_id) FROM sag.person GROUP BY cpf",
    )
    repository = repository_for(database)
    sessions = [await repository.load(person_id) for person_id in one_id_per_person]
    return [contract for session in sessions for contract in session.contract_ids]


async def test_every_contract_belongs_to_exactly_one_person(database: Database) -> None:
    owned = await contracts_owned_by_each_person(database)
    all_contracts = await SqlOracle(database).values("SELECT contractid FROM finance.contract")
    assert len(owned) == len(set(owned))
    assert set(owned) == all_contracts


async def test_every_invoice_status_in_the_database_has_translation(database: Database) -> None:
    statuses = await SqlOracle(database).values("SELECT DISTINCT status FROM finance.invoice")
    translated = {FinanceDialect.invoice_status(status) for status in statuses}
    assert translated == set(InvoiceStatus)

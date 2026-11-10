from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.requester_directory import SqlRequesterDirectory
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.support.sql_oracle import SqlOracle

STUDENT = "3000003"
OTHER_STUDENT = "3001224"
NOBODY = "0000000"
FULL_NAME = "SELECT full_name FROM sag.person WHERE person_id = :id"


async def directory_of(database: Database, person_id: str) -> SqlRequesterDirectory:
    session = await StudentSessionRepository(database).load(person_id)
    return SqlRequesterDirectory(RepositoryAdapter(database, session))


async def test_the_session_reads_the_name_of_its_own_person(database: Database) -> None:
    directory = await directory_of(database, STUDENT)
    assert {await directory.full_name_of(STUDENT)} == await SqlOracle().values(
        FULL_NAME, id=STUDENT
    )


async def test_the_name_of_another_person_is_the_same_as_a_missing_one(
    database: Database,
) -> None:
    directory = await directory_of(database, STUDENT)
    foreign = await directory.full_name_of(OTHER_STUDENT)
    missing = await directory.full_name_of(NOBODY)
    assert await SqlOracle().values(FULL_NAME, id=OTHER_STUDENT) != set()
    assert foreign is None
    assert foreign == missing

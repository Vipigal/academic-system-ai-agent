import pytest
from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.exc import DetachedInstanceError

from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository
from api.persistence.secretary.models import ProtocolRow

PERSON = "3032393"
REQUESTER_COLUMNS = ["requester_cpf", "requester_name"]


@pytest.mark.parametrize("attribute", REQUESTER_COLUMNS)
async def test_a_row_from_the_adapter_does_not_bring_the_requester(
    database: Database, attribute: str
) -> None:
    factory = database.db_session_factory
    session = await StudentSessionRepository(factory).load(PERSON)
    rows = await RepositoryAdapter(factory, session).fetch(select(ProtocolRow))
    assert rows
    assert attribute not in vars(rows[0])
    with pytest.raises(DetachedInstanceError):
        getattr(rows[0], attribute)


@pytest.mark.parametrize("attribute", REQUESTER_COLUMNS)
async def test_touching_the_requester_inside_a_session_raises_instead_of_loading(
    database: Database, attribute: str
) -> None:
    async with database.db_session_factory() as db:
        row = await db.scalar(select(ProtocolRow).limit(1))
        assert row is not None
        with pytest.raises(InvalidRequestError, match=f"{attribute}.*raiseload"):
            getattr(row, attribute)

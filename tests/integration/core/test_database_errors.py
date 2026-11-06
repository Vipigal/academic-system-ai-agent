import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from api.persistence.core.database import Database

PRIVATE_VALUE = "123.456.789-09"
FAILS_WITH_PARAMETERS = text("SELECT CAST(:cpf AS text), 1 / CAST(:zero AS integer)")


async def test_a_failed_statement_does_not_carry_its_parameters(database: Database) -> None:
    async with database.db_session_factory() as session:
        with pytest.raises(DBAPIError) as raised:
            await session.execute(FAILS_WITH_PARAMETERS, {"cpf": PRIVATE_VALUE, "zero": 0})

    assert PRIVATE_VALUE not in str(raised.value)

from datetime import UTC, datetime

import pytest

from api.domain.protocol.opening import ProtocolOpening
from api.domain.protocol.status import ProtocolStatus
from api.persistence.core.database import Database
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository
from api.persistence.secretary.protocol_writer import SqlProtocolWriter
from tests.integration.protocol.support import table_counts
from tests.integration.support.sql_oracle import SqlOracle

PERSON = "3000003"
MOMENT = datetime(2026, 10, 31, 3, 0, tzinfo=UTC)
FOREIGN_OPENING = ProtocolOpening(
    service_code="GEN-090",
    enrollment_reference="UniMontanhas_EAD:012378",
    unit_name="POLO BELO HORIZONTE - CENTRO",
    course_name="Administration",
    requester_name="Outra Pessoa",
    message="x",
    status=ProtocolStatus.OPEN,
    opened_at=MOMENT,
    due_at=MOMENT,
)


async def test_the_writer_refuses_an_enrollment_outside_the_session(database: Database) -> None:
    oracle = SqlOracle()
    before = await table_counts(oracle)
    session = await StudentSessionRepository(database).load(PERSON)
    writer = SqlProtocolWriter(RepositoryAdapter(database, session))
    with pytest.raises(OwnershipError):
        await writer.save(FOREIGN_OPENING)
    assert await table_counts(oracle) == before

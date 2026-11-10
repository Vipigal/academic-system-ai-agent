from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, update
from sqlalchemy.exc import DBAPIError

from api.persistence.agent.models import ConversationRow, MessageRow
from api.persistence.core import ownership_criteria
from api.persistence.core.database import Database
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.support.sql_oracle import SqlOracle

OWNER = "3001982"
OTHER = "3000071"
COUNTS = {
    "conversation": "SELECT count(*) FROM agent.conversation WHERE id = CAST(:id AS uuid)",
    "message": "SELECT count(*) FROM agent.message WHERE conversation_id = CAST(:id AS uuid)",
}


def message(conversation_id: UUID, position: int) -> MessageRow:
    return MessageRow(
        id=uuid4(),
        conversation_id=conversation_id,
        position=position,
        role="user",
        content="oi",
        model=None,
        tokens_in=None,
        tokens_out=None,
        latency_ms=None,
    )


async def adapter_of(database: Database, person_id: str) -> RepositoryAdapter:
    session = await StudentSessionRepository(database).load(person_id)
    return RepositoryAdapter(database, session)


async def count_of(table: str, conversation_id: UUID) -> int:
    return await SqlOracle().count(COUNTS[table], id=str(conversation_id))


async def test_batches_and_an_update_commit_together(database: Database) -> None:
    adapter = await adapter_of(database, OWNER)
    conversation = ConversationRow(id=uuid4(), person_id=OWNER)
    touch = (
        update(ConversationRow)
        .where(ConversationRow.id == conversation.id)
        .values(updated_at=func.now())
    )
    await adapter.write([conversation], [message(conversation.id, 1)], touch)
    assert await count_of("conversation", conversation.id) == 1
    assert await count_of("message", conversation.id) == 1


async def test_a_failing_step_rolls_back_the_earlier_ones(database: Database) -> None:
    adapter = await adapter_of(database, OWNER)
    conversation = ConversationRow(id=uuid4(), person_id=OWNER)
    twice = [message(conversation.id, 1), message(conversation.id, 1)]
    with pytest.raises(DBAPIError):
        await adapter.write([conversation], twice)
    assert await count_of("conversation", conversation.id) == 0


async def test_the_update_carries_the_owner_of_the_session(database: Database) -> None:
    conversation = ConversationRow(id=uuid4(), person_id=OWNER)
    await (await adapter_of(database, OWNER)).write([conversation])
    stranger = await adapter_of(database, OTHER)
    foreign = (
        update(ConversationRow).where(ConversationRow.id == conversation.id).values(person_id=OTHER)
    )
    await stranger.write(foreign)
    stored = await SqlOracle().values(
        "SELECT person_id FROM agent.conversation WHERE id = CAST(:id AS uuid)",
        id=str(conversation.id),
    )
    assert stored == {OWNER}


async def test_a_batch_of_an_unregistered_table_writes_nothing(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = await adapter_of(database, OWNER)
    conversation = ConversationRow(id=uuid4(), person_id=OWNER)
    monkeypatch.delitem(ownership_criteria.OWNERSHIP_BY_TABLE, MessageRow.__table__)
    with pytest.raises(OwnershipError):
        await adapter.write([conversation], [message(conversation.id, 1)])
    assert await count_of("conversation", conversation.id) == 0

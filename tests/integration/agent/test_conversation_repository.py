from uuid import UUID

import pytest
from sqlalchemy import select

from api.domain.conversation.errors import ConversationNotFoundError
from api.domain.conversation.message import Message, MessageRole, ToolCall
from api.persistence.agent.models import ConversationRow
from api.persistence.agent.repository import SqlConversationRepository
from api.persistence.core.database import Database
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.support.sql_oracle import SqlOracle

OWNER = "3001982"
OTHER = "3000071"
WINDOW = 20
CALL = ToolCall(
    id="call_1",
    name="list_invoices",
    arguments={"status": "open"},
    result={"status": "ok", "data": [1, 2]},
    status="ok",
    duration_ms=12,
)


def user(text: str) -> Message:
    return Message(MessageRole.USER, text)


def assistant(text: str, *calls: ToolCall) -> Message:
    return Message(
        MessageRole.ASSISTANT,
        text,
        tool_calls=calls,
        model="gpt-test",
        tokens_in=10,
        tokens_out=5,
        latency_ms=300,
    )


async def repository_of(database: Database, person_id: str) -> SqlConversationRepository:
    session = await StudentSessionRepository(database.db_session_factory).load(person_id)
    return SqlConversationRepository(RepositoryAdapter(database.db_session_factory, session))


@pytest.fixture
async def repository(database: Database) -> SqlConversationRepository:
    return await repository_of(database, OWNER)


async def test_stores_and_reads_a_conversation_with_tool_calls(
    repository: SqlConversationRepository,
) -> None:
    conversation = await repository.create(OWNER)
    await repository.append(conversation, [user("quais faturas?"), assistant("duas", CALL)])
    messages = await repository.window(conversation, WINDOW)
    assert [message.role for message in messages] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert messages[1].tool_calls == (CALL,)
    assert messages[1].model == "gpt-test"


async def test_the_window_keeps_the_last_messages_with_their_tool_results(
    repository: SqlConversationRepository,
) -> None:
    conversation = await repository.create(OWNER)
    for turn in range(3):
        await repository.append(conversation, [user(f"p{turn}"), assistant(f"r{turn}", CALL)])
    messages = await repository.window(conversation, 3)
    assert [message.content for message in messages] == ["r1", "p2", "r2"]
    assert messages[0].tool_calls == (CALL,)
    assert messages[2].tool_calls == (CALL,)


async def test_the_window_at_the_limit_returns_everything(
    repository: SqlConversationRepository,
) -> None:
    conversation = await repository.create(OWNER)
    await repository.append(conversation, [user("a"), assistant("b")])
    assert len(await repository.window(conversation, 2)) == 2
    assert len(await repository.window(conversation, 1)) == 1


async def test_another_persons_conversation_and_a_missing_one_fail_the_same_way(
    database: Database,
    repository: SqlConversationRepository,
) -> None:
    conversation = await repository.create(OWNER)
    stranger = await repository_of(database, OTHER)
    missing = UUID(int=0)
    for target in (conversation, missing):
        with pytest.raises(ConversationNotFoundError):
            await stranger.window(target, WINDOW)
        with pytest.raises(ConversationNotFoundError):
            await stranger.append(target, [user("x")])


async def test_a_conversation_is_created_only_for_a_person_of_the_session(
    database: Database,
) -> None:
    repository = await repository_of(database, OWNER)
    with pytest.raises(OwnershipError):
        await repository.create(OTHER)


async def test_the_person_id_lives_only_in_the_conversation(
    repository: SqlConversationRepository,
) -> None:
    conversation = await repository.create(OWNER)
    await repository.append(conversation, [user("a"), assistant("b", CALL)])
    columns = await SqlOracle().values(
        "SELECT table_name FROM information_schema.columns "
        "WHERE table_schema = 'agent' AND column_name = 'person_id'"
    )
    assert columns == {"conversation"}
    stored = await SqlOracle().values(
        "SELECT person_id FROM agent.conversation WHERE id = CAST(:id AS uuid)",
        id=str(conversation),
    )
    assert stored == {OWNER}


async def test_the_stored_result_is_what_the_model_saw(
    repository: SqlConversationRepository,
) -> None:
    conversation = await repository.create(OWNER)
    await repository.append(conversation, [user("a"), assistant("b", CALL)])
    stored = await SqlOracle().values(
        "SELECT jsonb_object_keys(t.result) FROM agent.tool_call t "
        "JOIN agent.message m ON m.id = t.message_id "
        "WHERE m.conversation_id = CAST(:id AS uuid)",
        id=str(conversation),
    )
    assert stored == set(CALL.result or {})


async def test_the_adapter_hides_the_conversation_from_other_people(database: Database) -> None:
    conversation = await (await repository_of(database, OWNER)).create(OWNER)
    session = await StudentSessionRepository(database.db_session_factory).load(OTHER)
    adapter = RepositoryAdapter(database.db_session_factory, session)
    statement = select(ConversationRow).where(ConversationRow.id == conversation)
    assert await adapter.fetch(statement) == []

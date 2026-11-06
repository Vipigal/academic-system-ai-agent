from http import HTTPStatus
from uuid import uuid4

import httpx
import pytest

from api.persistence.core.database import Database
from tests.integration.chat import chat_client as support
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.support.sql_oracle import SqlOracle
from tests.unit.agent.agent_support import RecordingModel, answer, call

QUESTION = "Quanto devo?"
OWNER_OF = "SELECT person_id FROM agent.conversation WHERE id = cast(:id AS uuid)"
RESULTS_OF = """
    SELECT tool_call.result::text
    FROM agent.tool_call
    JOIN agent.message ON message.id = tool_call.message_id
    WHERE message.conversation_id = cast(:id AS uuid)
"""
PROPOSAL = call("propose_protocol", {"service": "GEN-090", "message": "Pedido"})


@pytest.fixture
def app(database: Database) -> ChatApp:
    return ChatApp(database, RecordingModel(responses=[answer()]), settings_with())


async def attempts_on(client: httpx.AsyncClient, alien: str) -> list[httpx.Response]:
    other = await support.ChatClient.logged_in(client, support.OTHER_STUDENT)
    identifiers = (alien, str(uuid4()), "not-a-uuid")
    return [await other.send(identifier, QUESTION) for identifier in identifiers]


async def test_alien_absent_and_malformed_conversations_get_the_same_not_found(
    app: ChatApp, database: Database
) -> None:
    async with app.client() as client:
        owner = await support.ChatClient.logged_in(client)
        alien = await owner.create_conversation()
        responses = await attempts_on(client, alien)

    assert {response.status_code for response in responses} == {HTTPStatus.NOT_FOUND}
    assert len({response.text for response in responses}) == 1
    assert not await support.history_of(database, alien)


async def test_the_conversation_is_created_with_the_owner_of_the_token(app: ChatApp) -> None:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        conversation = await chat.create_conversation()

    assert await SqlOracle().values(OWNER_OF, id=conversation) == {support.STUDENT_PERSON}


async def test_a_body_on_creation_cannot_choose_the_owner_or_the_id(app: ChatApp) -> None:
    chosen = str(uuid4())
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        response = await client.post(
            "/conversations", json={"id": chosen, "person_id": "3000071"}, headers=chat.headers
        )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()["id"] != chosen
    assert await SqlOracle().values(OWNER_OF, id=response.json()["id"]) == {support.STUDENT_PERSON}


async def test_without_a_token_both_routes_are_unauthorized(app: ChatApp) -> None:
    async with app.client() as client:
        created = await client.post("/conversations")
        sent = await support.ChatClient(client).send(str(uuid4()), QUESTION)

    assert created.status_code == sent.status_code == HTTPStatus.UNAUTHORIZED


async def test_client_only_goes_out_in_the_stream_and_stays_out_of_the_history(
    database: Database,
) -> None:
    app = ChatApp(database, RecordingModel(responses=[PROPOSAL, answer()]), settings_with())
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        done = await chat.exchange(support.user_message("Quero abrir um protocolo"))

    stored = next(iter(await SqlOracle().values(RESULTS_OF, id=done.conversation)))
    assert support.client_token_of(done)
    assert support.client_token_of(done) not in stored
    assert "client_only" not in stored

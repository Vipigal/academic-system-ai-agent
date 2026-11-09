from http import HTTPStatus

import pytest

from api.infrastructure.rate_limiter import RedisRateLimiter
from api.persistence.core.database import Database
from tests.integration.chat import chat_client as support
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.unit.agent.agent_support import RecordingModel, answer
from tests.unit.infrastructure.memory_redis import MemoryRedis

QUESTION = "Quanto devo?"
HOUR = "3600"
QUOTA_HEADERS = ("ratelimit-limit", "ratelimit-remaining", "ratelimit-reset")


@pytest.fixture
def model() -> RecordingModel:
    return RecordingModel(responses=[answer()])


@pytest.fixture
def app(database: Database, model: RecordingModel) -> ChatApp:
    limiter = RedisRateLimiter(MemoryRedis(), limit=1)
    return ChatApp(database, model, settings_with(), rate_limiter=limiter)


def quota_of(headers: dict[str, str]) -> tuple[str, ...]:
    return tuple(headers.get(name, "") for name in QUOTA_HEADERS)


async def test_an_accepted_message_streams_with_what_is_left_of_the_quota(app: ChatApp) -> None:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        response = await chat.send(await chat.create_conversation(), QUESTION)

    assert response.status_code == HTTPStatus.OK
    assert quota_of(dict(response.headers)) == ("1", "0", HOUR)


async def test_over_the_limit_the_message_is_refused_before_the_model(
    app: ChatApp, model: RecordingModel
) -> None:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        conversation = await chat.create_conversation()
        await chat.send(conversation, QUESTION)
        refused = await chat.send(conversation, QUESTION)

    assert refused.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert refused.headers["retry-after"] == HOUR
    assert quota_of(dict(refused.headers)) == ("1", "0", HOUR)
    assert len(model.seen) == 1


async def test_a_malformed_message_does_not_spend_the_quota(app: ChatApp) -> None:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        conversation = await chat.create_conversation()
        rejected = await chat.send(conversation, "   ")
        accepted = await chat.send(conversation, QUESTION)

    assert rejected.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert accepted.status_code == HTTPStatus.OK


async def test_creating_conversations_does_not_spend_the_quota(app: ChatApp) -> None:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        await chat.create_conversation()
        response = await chat.send(await chat.create_conversation(), QUESTION)

    assert response.status_code == HTTPStatus.OK


async def test_without_a_limiter_the_chat_sends_no_quota_headers(
    database: Database, model: RecordingModel
) -> None:
    async with ChatApp(database, model, settings_with()).client() as client:
        chat = await support.ChatClient.logged_in(client)
        response = await chat.send(await chat.create_conversation(), QUESTION)

    assert response.status_code == HTTPStatus.OK
    assert quota_of(dict(response.headers)) == ("", "", "")

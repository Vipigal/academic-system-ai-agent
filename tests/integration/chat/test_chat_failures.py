import logging
from collections.abc import Iterator

import pytest

from api.infrastructure.logging import JsonFormatter
from api.persistence.agent.repository import SqlConversationRepository
from api.persistence.core.database import Database
from api.presentation.http.ui_stream import GENERIC_ERROR
from tests.integration.chat import chat_client as support
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.chat.scripted_models import FailingModel, GatedModel
from tests.unit.agent.agent_support import RecordingModel, answer, call

CLOSING = ["error", "finish-step", "finish"]
QUESTION = "Quanto devo?"
ASKED = support.user_message(QUESTION)
COLLIDING = "Colide"


class CapturedLog(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(JsonFormatter().format(record))


@pytest.fixture
def chat_log() -> Iterator[CapturedLog]:
    handler = CapturedLog()
    logger = logging.getLogger("api.application.chat.service")
    logger.addHandler(handler)
    yield handler
    logger.removeHandler(handler)


def assert_failed_generically(done: support.Exchange) -> None:
    assert support.kinds_of(done.chunks)[-3:] == CLOSING
    assert support.first_of(done.chunks, "error")["errorText"] == GENERIC_ERROR


async def exchange_with(app: ChatApp) -> support.Exchange:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        return await chat.exchange(ASKED)


async def second_message_with_stale_position(app: ChatApp) -> support.Exchange:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        conversation = await chat.create_conversation()
        await chat.send(conversation, QUESTION)
        return support.Exchange(conversation, await chat.send(conversation, COLLIDING))


async def test_a_provider_failure_emits_a_generic_error_and_records_nothing(
    database: Database,
) -> None:
    model = FailingModel(responses=[answer()])
    done = await exchange_with(ChatApp(database, model, settings_with()))

    assert_failed_generically(done)
    assert "segredo-interno" not in done.response.text
    assert not await support.history_of(database, done.conversation)


async def test_a_timeout_closes_the_open_text_and_records_nothing(database: Database) -> None:
    settings = settings_with(agent_timeout_seconds=0.05)
    done = await exchange_with(ChatApp(database, GatedModel(responses=[answer()]), settings))

    assert_failed_generically(done)
    assert "text-end" in support.kinds_of(done.chunks)
    assert not await support.history_of(database, done.conversation)


async def test_the_model_call_limit_finishes_the_turn_and_records_it(database: Database) -> None:
    model = RecordingModel(responses=[call("get_financial_summary"), answer()])
    settings = settings_with(agent_model_call_limit=1)
    done = await exchange_with(ChatApp(database, model, settings))

    stored = await support.history_of(database, done.conversation)
    assert "error" not in support.kinds_of(done.chunks)
    assert stored[-1].content == support.transmitted_text(done.chunks)
    assert len(stored[-1].tool_calls) == 1


async def test_a_position_collision_becomes_a_generic_error_with_the_trace_in_the_log(
    database: Database, monkeypatch: pytest.MonkeyPatch, chat_log: CapturedLog
) -> None:
    async def stale_position(*_: object) -> int:
        return 1

    monkeypatch.setattr(SqlConversationRepository, "_next_position", stale_position)
    app = ChatApp(database, RecordingModel(responses=[answer()]), settings_with())
    done = await second_message_with_stale_position(app)

    assert_failed_generically(done)
    assert "IntegrityError" not in done.response.text
    logged = next(line for line in chat_log.lines if "ConversationConflictError" in line)
    assert '"trace_id": ""' not in logged
    stored = await support.history_of(database, done.conversation)
    assert COLLIDING not in [message.content for message in stored]

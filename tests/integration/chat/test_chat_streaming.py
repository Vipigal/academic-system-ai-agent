import asyncio

import pytest
from starlette.requests import ClientDisconnect

from api.persistence.core.database import Database
from tests.integration.chat import chat_client as support
from tests.integration.chat.asgi_call import AsgiCall
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.chat.scripted_models import FIRST_WORD, SECOND_WORD, GatedModel
from tests.unit.agent.agent_support import answer

PATIENCE_SECONDS = 5
DONE = f"{support.DONE_FRAME}\n\n"


def position_of(word: str, frames: list[str]) -> int:
    return next(index for index, frame in enumerate(frames) if word in frame)


@pytest.fixture
def model() -> GatedModel:
    return GatedModel(responses=[answer()])


@pytest.fixture
def app(database: Database, model: GatedModel) -> ChatApp:
    return ChatApp(database, model, settings_with())


async def test_events_leave_while_the_model_is_still_answering(
    app: ChatApp, model: GatedModel
) -> None:
    asgi = await AsgiCall.opened_in(app)

    def release_on_first_word(frame: str) -> None:
        if FIRST_WORD in frame:
            model.gate.set()

    asgi.on_frame = release_on_first_word
    async with asyncio.timeout(PATIENCE_SECONDS):
        await asgi.post_chat()

    assert asgi.frames[-1] == DONE
    assert position_of(FIRST_WORD, asgi.frames) < position_of(SECOND_WORD, asgi.frames)


async def test_a_client_that_disconnects_records_nothing(app: ChatApp, database: Database) -> None:
    asgi = await AsgiCall.opened_in(app)

    def disconnect_on_first_word(frame: str) -> None:
        if FIRST_WORD in frame:
            asgi.disconnected.set()

    asgi.on_frame = disconnect_on_first_word
    async with asyncio.timeout(PATIENCE_SECONDS):
        await asgi.post_chat()

    assert asgi.frames[-1] != DONE
    assert not await support.history_of(database, asgi.conversation)


async def test_a_send_that_breaks_mid_stream_records_nothing(
    app: ChatApp, database: Database
) -> None:
    asgi = await AsgiCall.opened_in(app, spec_version="2.4")

    def break_on_first_word(frame: str) -> None:
        if FIRST_WORD in frame:
            raise OSError

    asgi.on_frame = break_on_first_word
    with pytest.raises(ClientDisconnect):
        await asgi.post_chat()

    assert not await support.history_of(database, asgi.conversation)

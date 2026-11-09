import asyncio
import gc
import logging

import pytest
from starlette.requests import ClientDisconnect

from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from tests.integration.chat.asgi_call import AsgiCall
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.chat.scripted_models import FIRST_WORD, GatedModel
from tests.unit.agent.agent_support import answer

PATIENCE_SECONDS = 5
CONTEXT_ERRORS = ("different Context", "Failed to detach")


def context_errors_in(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [line for line in caplog.messages if any(error in line for error in CONTEXT_ERRORS)]


@pytest.fixture
def app(database: Database, tracing: Tracing) -> ChatApp:
    return ChatApp(database, GatedModel(responses=[answer()]), settings_with(), tracing)


async def test_a_disconnect_keeps_the_trace_context_clean(
    app: ChatApp, caplog: pytest.LogCaptureFixture
) -> None:
    asgi = await AsgiCall.opened_in(app)

    def disconnect_on_first_word(frame: str) -> None:
        if FIRST_WORD in frame:
            asgi.disconnected.set()

    asgi.on_frame = disconnect_on_first_word
    with caplog.at_level(logging.WARNING):
        async with asyncio.timeout(PATIENCE_SECONDS):
            await asgi.post_chat()

    assert FIRST_WORD in str(asgi.frames)
    assert not context_errors_in(caplog)


async def test_a_stream_abandoned_mid_way_keeps_the_trace_context_clean(
    app: ChatApp, caplog: pytest.LogCaptureFixture
) -> None:
    asgi = await AsgiCall.opened_in(app, spec_version="2.4")

    def break_on_first_word(frame: str) -> None:
        if FIRST_WORD in frame:
            raise OSError

    asgi.on_frame = break_on_first_word
    with caplog.at_level(logging.WARNING), pytest.raises(ClientDisconnect):
        await asgi.post_chat()
    gc.collect()
    await asyncio.sleep(0.05)

    assert not context_errors_in(caplog)

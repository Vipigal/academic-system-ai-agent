import asyncio
from http import HTTPStatus

import pytest

from api.persistence.core.database import Database
from tests.integration.chat import chat_client as support
from tests.integration.chat.asgi_call import AsgiCall
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.chat.scripted_models import FIRST_WORD, GatedModel
from tests.unit.agent.agent_support import answer

PATIENCE_SECONDS = 5


@pytest.fixture
def model() -> GatedModel:
    return GatedModel(responses=[answer()])


async def test_after_a_disconnect_the_provider_gate_is_free_for_the_next_turn(
    database: Database, model: GatedModel
) -> None:
    app = ChatApp(database, model, settings_with(agent_max_concurrency=1))
    asgi = await AsgiCall.opened_in(app)
    asgi.on_frame = lambda frame: asgi.disconnected.set() if FIRST_WORD in frame else None
    async with asyncio.timeout(PATIENCE_SECONDS):
        await asgi.post_chat()
    model.gate.set()

    async with app.client() as client, asyncio.timeout(PATIENCE_SECONDS):
        chat = await support.ChatClient.logged_in(client)
        response = await chat.exchange(support.user_message("Quanto devo?"))

    assert response.response.status_code == HTTPStatus.OK
    assert support.kinds_of(response.chunks)[-1] == "finish"

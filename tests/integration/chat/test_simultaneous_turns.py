import asyncio
from http import HTTPStatus

import httpx

from api.persistence.core.database import Database
from tests.integration.chat import chat_client as support
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.chat.slow_model import SlowModel
from tests.unit.agent.agent_support import answer

TURNS = 20


async def simultaneous_turns(app: ChatApp) -> list[httpx.Response]:
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        conversations = [await chat.create_conversation() for _ in range(TURNS)]
        return list(await asyncio.gather(*(chat.send(each, "Oi") for each in conversations)))


async def test_simultaneous_turns_do_not_queue_in_lots(database: Database) -> None:
    model = SlowModel(responses=[answer()], expected=TURNS)

    responses = await simultaneous_turns(ChatApp(database, model, settings_with()))

    assert {response.status_code for response in responses} == {HTTPStatus.OK}
    assert max(model.peaks) == TURNS

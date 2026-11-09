from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from tests.integration.chat import chat_client as support
from tests.integration.chat.chat_app import ChatApp
from tests.integration.chat.chat_settings import settings_with
from tests.integration.chat.span_sink import SpanSink
from tests.unit.agent.agent_support import RecordingModel, answer, call

PROPOSAL = call("propose_protocol", {"action": "informacoes_gerais", "enrollment": support.STUDENT})


async def test_what_leaves_for_langfuse_carries_the_turn_without_client_only(
    database: Database, tracing: Tracing, sink: SpanSink
) -> None:
    model = RecordingModel(responses=[PROPOSAL, answer()])
    app = ChatApp(database, model, settings_with(), tracing)
    async with app.client() as client:
        chat = await support.ChatClient.logged_in(client)
        token = support.client_token_of(await chat.exchange(support.user_message("Protocolo")))
    tracing.flush()

    assert b"chat.turn" in sink.received
    assert b"propose_protocol" in sink.received
    assert token.encode() not in sink.received
    assert b"client_only" not in sink.received

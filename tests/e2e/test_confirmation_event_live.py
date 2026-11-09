from http import HTTPStatus

import pytest

from tests.e2e.e2e_settings import live_settings
from tests.e2e.running_api import running_api
from tests.e2e.student_flow import PROPOSE_TOOL, StudentFlow, tools_called
from tests.integration.chat.chat_client import transmitted_text
from tests.integration.protocol.rolled_back import RolledBackBank

DECLARATION_REQUEST = (
    "Quero uma declaração de matrícula do meu curso. Prepare o pedido para eu confirmar no card."
)
FOLLOW_UP = "Meu pedido foi aberto?"


@pytest.mark.live
async def test_after_the_confirmation_the_model_knows_the_request_is_open(
    bank: RolledBackBank,
) -> None:
    with running_api(bank, live_settings()) as api:
        result = await StudentFlow(api.client, DECLARATION_REQUEST, FOLLOW_UP).run()

    assert PROPOSE_TOOL in tools_called(result.proposal)
    assert result.confirmation.status_code == HTTPStatus.CREATED
    assert result.number in transmitted_text(result.listing)

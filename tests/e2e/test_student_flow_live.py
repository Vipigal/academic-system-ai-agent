from http import HTTPStatus

import pytest

from tests.e2e.e2e_settings import live_settings
from tests.e2e.running_api import running_api
from tests.e2e.student_flow import LIST_TOOL, PROPOSE_TOOL, StudentFlow, outputs_text, tools_called
from tests.integration.protocol.rolled_back import RolledBackBank

PROPOSAL_TEXT = (
    "Quero abrir o pedido de serviço GEN-090, sem taxa, com a mensagem: Pedido do aluno. "
    "Prepare a proposta para eu confirmar."
)
LISTING_TEXT = "Liste os meus protocolos em andamento."


@pytest.mark.live
async def test_the_whole_flow_with_the_real_model(bank: RolledBackBank) -> None:
    with running_api(bank, live_settings()) as api:
        result = await StudentFlow(api.client, PROPOSAL_TEXT, LISTING_TEXT).run()

    assert PROPOSE_TOOL in tools_called(result.proposal)
    assert result.confirmation.status_code == HTTPStatus.CREATED
    assert LIST_TOOL in tools_called(result.listing)
    assert result.number in outputs_text(result.listing)

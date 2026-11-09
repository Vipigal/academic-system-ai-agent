import pytest

from api.application.protocol.dto.proposal import Proposal
from api.application.shared.tool_result import ToolResult, ToolStatus
from api.bootstrap.containers import Containers
from api.domain.ports.protocol import ProposalSigner
from api.domain.protocol.action import ProtocolAction
from api.persistence.core.database import Database
from tests.integration.protocol.confirmation_app import ConfirmationApp
from tests.integration.protocol.confirmation_settings import settings_with

PERSON = "3000003"
STUDENT = "UniSaoPaulo:180017"
INFORMATION = ProtocolAction.INFORMACOES_GERAIS


async def proposed(database: Database) -> tuple[ConfirmationApp, ToolResult[Proposal]]:
    app = ConfirmationApp(database)
    protocols = await app.protocols_of(PERSON)
    return app, await protocols.propose_protocol(INFORMATION, STUDENT, None)


async def test_the_token_and_the_confirmation_go_to_the_client(database: Database) -> None:
    app, result = await proposed(database)

    assert result.status is ToolStatus.OK
    client_only = result.client_only or {}
    token = client_only.get("token")
    assert isinstance(token, str)
    assert app.signer.verify(token) is not None
    assert set(client_only.get("confirmation") or ()) == {"question", "effect", "limit", "word"}


async def test_the_json_that_goes_to_the_model_has_no_token_and_no_confirmation(
    database: Database,
) -> None:
    _, result = await proposed(database)

    dumped = result.model_dump_json()
    assert result.client_only is not None
    assert str(result.client_only["token"]) not in dumped
    assert {"client_only", "token", "confirmation", "question"}.isdisjoint(dumped.split('"'))


async def test_refusals_and_candidates_carry_no_token(database: Database) -> None:
    app = ConfirmationApp(database)
    protocols = await app.protocols_of(PERSON)

    refused = await protocols.propose_protocol(
        ProtocolAction.TRANCAR_CURSO_INTEIRO, STUDENT, "Direito Empresarial"
    )
    missing = await protocols.propose_protocol(INFORMATION, "UniSaoPaulo:000000", None)

    assert (refused.status, missing.status) == (ToolStatus.REFUSED, ToolStatus.NOT_FOUND)
    assert (refused.client_only, missing.client_only) == (None, None)


async def test_a_missing_proposal_secret_fails_closed() -> None:
    container = Containers.students(settings_with(proposal_secret=None))
    with pytest.raises(ValueError, match="secret"):
        await container.get(ProposalSigner)
    await container.close()

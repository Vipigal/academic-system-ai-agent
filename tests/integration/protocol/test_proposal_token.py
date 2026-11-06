import pytest

from api.application.shared.tool_result import ToolStatus
from api.bootstrap.protocol_providers import ProtocolProviders
from api.persistence.core.database import Database
from tests.integration.protocol.confirmation_app import ConfirmationApp, settings_with

PERSON = "3000003"


async def test_the_token_goes_to_the_client(database: Database) -> None:
    app = ConfirmationApp(database)
    services = await app.students().services_of(PERSON)
    result = await services.protocol().propose_protocol("GEN-090", None, "Pedido")
    assert result.status is ToolStatus.OK
    assert result.client_only is not None
    assert app.signer.verify(result.client_only["token"]) is not None


async def test_the_json_that_goes_to_the_model_has_no_token(database: Database) -> None:
    app = ConfirmationApp(database)
    services = await app.students().services_of(PERSON)
    result = await services.protocol().propose_protocol("GEN-090", None, "Pedido")
    assert result.client_only is not None
    assert result.client_only["token"] not in result.model_dump_json()
    assert "client_only" not in result.model_dump_json()
    assert "token" not in result.model_dump_json()


async def test_refusals_and_candidates_carry_no_token(database: Database) -> None:
    app = ConfirmationApp(database)
    services = await app.students().services_of(PERSON)
    refused = await services.protocol().propose_protocol("DOC-002", None, "Pedido")
    missing = await services.protocol().propose_protocol("passaporte", None, "Pedido")
    assert (refused.client_only, missing.client_only) == (None, None)


def test_a_missing_proposal_secret_fails_closed() -> None:
    with pytest.raises(ValueError, match="secret"):
        ProtocolProviders.signer_of(settings_with(proposal_secret=None))

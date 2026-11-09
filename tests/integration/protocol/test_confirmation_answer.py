from collections.abc import AsyncIterator
from http import HTTPStatus
from uuid import uuid4

import pytest

from api.domain.conversation.message import MessageRole
from api.domain.protocol.proposal import SignedProposal
from tests.integration.protocol.confirmation_app import ConfirmationApp, confirmed_on
from tests.integration.protocol.information_request import (
    DECLARATION,
    TYPED,
    WRITTEN,
    history_for,
)
from tests.integration.protocol.rolled_back import RolledBackBank, rolled_back
from tests.integration.support.sql_oracle import admin_engine

STUDENT = "UniSaoPaulo:180017"
PERSON = "3000003"
ONLINE_PERSON = "3001224"
FREE_SERVICE = "GEN-090"
PAID_SERVICE = "DOC-002"
RENEGOTIATION = "FIN-031"
CREATED_CONVERSATION = {"agent.conversation": ("1", "0", "0")}
NOT_FOUND_BODY = '{"detail":"Not Found"}'
INTERACTION_MESSAGE = "SELECT message FROM secretary.protocol_interaction WHERE protocol = :number"


@pytest.fixture
async def bank() -> AsyncIterator[RolledBackBank]:
    async with rolled_back(admin_engine(), "SET LOCAL ROLE api") as rolled:
        yield rolled


@pytest.fixture
def app(bank: RolledBackBank) -> ConfirmationApp:
    return ConfirmationApp(bank.database)


async def test_a_simple_service_records_the_fixed_text_and_not_the_message(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    token = app.signer.sign(SignedProposal(PERSON, STUDENT, DECLARATION.code))
    response, _ = await app.confirmed_by(STUDENT, PERSON, token, WRITTEN)
    number = response.json()["protocol_number"]
    assert await bank.as_admin(INTERACTION_MESSAGE, number=number) == [(DECLARATION.request_text,)]


async def test_the_confirmation_event_joins_the_conversation_without_the_typed_text(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    token = await app.proposal_of(PERSON, STUDENT)
    response, conversation = await app.confirmed_by(STUDENT, PERSON, token, WRITTEN)
    [event] = await history_for(bank.database, PERSON, conversation)
    assert event.role is MessageRole.SYSTEM_EVENT
    assert response.json()["protocol_number"] in event.content
    assert TYPED not in event.content


async def test_a_conversation_out_of_reach_gets_the_same_404_and_writes_nothing(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    alien = await app.conversation_of(ONLINE_PERSON)
    refused = await confirmed_on(
        app, STUDENT, await app.proposal_of(PERSON, STUDENT), (alien, str(uuid4()), "nao-e-uuid")
    )
    assert {(response.status_code, response.text) for response in refused} == {
        (HTTPStatus.NOT_FOUND, NOT_FOUND_BODY)
    }
    assert await bank.writes() == CREATED_CONVERSATION


async def test_a_paid_service_without_an_action_gets_the_same_404_and_writes_nothing(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    token = app.signer.sign(SignedProposal(PERSON, STUDENT, PAID_SERVICE))
    response, _ = await app.confirmed_by(STUDENT, PERSON, token, {})
    assert (response.status_code, response.text) == (HTTPStatus.NOT_FOUND, NOT_FOUND_BODY)
    assert await bank.writes() == CREATED_CONVERSATION


@pytest.mark.parametrize(
    ("service", "answer", "reason"),
    [
        pytest.param(FREE_SERVICE, {"message": " "}, "empty_message", id="blank-free-text"),
        pytest.param(FREE_SERVICE, {"message": "x" * 4001}, "message_too_long", id="too-long"),
        pytest.param(
            RENEGOTIATION, {"confirmation_word": "cancelar"}, "confirmation_word", id="word"
        ),
    ],
)
async def test_a_refused_confirmation_is_unprocessable_and_writes_nothing(
    app: ConfirmationApp, bank: RolledBackBank, service: str, answer: dict[str, str], reason: str
) -> None:
    token = app.signer.sign(SignedProposal(PERSON, STUDENT, service))
    response, _ = await app.confirmed_by(STUDENT, PERSON, token, answer)
    assert (response.status_code, response.json()) == (
        HTTPStatus.UNPROCESSABLE_ENTITY,
        {"detail": reason},
    )
    assert await bank.writes() == CREATED_CONVERSATION


async def test_the_word_is_accepted_in_any_case(app: ConfirmationApp) -> None:
    token = app.signer.sign(SignedProposal(PERSON, STUDENT, RENEGOTIATION))
    response, _ = await app.confirmed_by(
        STUDENT, PERSON, token, {"confirmation_word": " renegociar "}
    )
    assert response.status_code == HTTPStatus.CREATED

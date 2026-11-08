from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import pytest

from api.application.shared.page import FIRST_PAGE
from api.domain.protocol.proposal import SignedProposal
from tests.integration.protocol.confirmation_app import ConfirmationApp, confirm, login
from tests.integration.protocol.information_request import REQUEST_TEXT
from tests.integration.protocol.rolled_back import RolledBackBank, rolled_back
from tests.integration.support.sql_oracle import admin_engine

STUDENT = "UniSaoPaulo:180017"
PERSON = "3000003"
OTHER_STUDENT = "UniMontanhas:070017"
ONLINE_STUDENT = "UniMontanhas_EAD:012378"
ONLINE_PERSON = "3001224"
FREE_SERVICE = "GEN-090"
SLA_HOURS = 72
PAID_SERVICE = "DOC-002"
OPENED = datetime(2026, 10, 31, 3, 0, tzinfo=UTC)
OPENED_TEXT = "2026-10-31T03:00:00Z"
DUE_TEXT = "2026-11-03T03:00:00Z"
ONE_INSERT = ("1", "0", "0")
NOT_FOUND_BODY = '{"detail":"Not Found"}'
WRITES = """
    SELECT schemaname || '.' || relname, n_tup_ins::text, n_tup_upd::text, n_tup_del::text
    FROM pg_stat_xact_user_tables
    WHERE n_tup_ins + n_tup_upd + n_tup_del > 0
"""
PROTOCOL_COLUMNS = """
    SELECT stu_id, requester_type, unit_code, demand, demand_status, channel, priority,
           sla_breached, opened_at, sla_due_at, first_response_at, closed_at, resolution,
           demand_analyst
    FROM secretary.protocol WHERE protocol = :number
"""
PROTOCOL_REQUESTER = """
    SELECT requester_cpf, requester_name FROM secretary.protocol WHERE protocol = :number
"""
PERSON_DATA = (
    r"SELECT regexp_replace(cpf, '\D', '', 'g'), full_name FROM sag.person WHERE person_id = :id"
)
HISTORY = """
    SELECT seq, from_status, to_status, changed_at, changed_by
    FROM secretary.protocol_status_history WHERE protocol = :number
"""
INTERACTION = """
    SELECT author_type, author, message, is_internal_note, created_at
    FROM secretary.protocol_interaction WHERE protocol = :number
"""
INTERACTION_NUMBER = """
    SELECT interaction_id, (SELECT last_value::text FROM agent.protocol_interaction_seq)
    FROM secretary.protocol_interaction WHERE protocol = :number
"""


@pytest.fixture
async def bank() -> AsyncIterator[RolledBackBank]:
    async with rolled_back(admin_engine(), "SET LOCAL ROLE api") as rolled:
        yield rolled


@pytest.fixture
def app(bank: RolledBackBank) -> ConfirmationApp:
    return ConfirmationApp(bank.database)


async def written_tables(bank: RolledBackBank) -> dict[str | None, tuple[str | None, ...]]:
    return {row[0]: row[1:] for row in await bank.as_admin(WRITES)}


async def opened_number(app: ConfirmationApp, student: str, person: str) -> str:
    token = await app.proposal_of(person, student)
    async with app.client() as client:
        response = await confirm(client, await login(client, student), token)
    assert response.status_code == HTTPStatus.CREATED
    return str(response.json()["protocol_number"])


async def test_the_app_runs_as_the_restricted_role(bank: RolledBackBank) -> None:
    assert await bank.as_app("SELECT current_user") == "api"


async def test_confirmation_answers_with_the_number_status_and_deadline(
    app: ConfirmationApp,
) -> None:
    token = await app.proposal_of(PERSON, STUDENT)
    async with app.client() as client:
        response = await confirm(client, await login(client, STUDENT), token)
    assert response.status_code == HTTPStatus.CREATED
    assert set(response.json()) == {"protocol_number", "status", "sla_due_at"}
    assert response.json()["status"] == "open"
    due = datetime.fromisoformat(response.json()["sla_due_at"])
    assert due == OPENED + timedelta(hours=SLA_HOURS)


async def test_the_numbers_come_from_the_sequences(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    number = await opened_number(app, STUDENT, PERSON)
    sequence = await bank.as_admin("SELECT last_value::text FROM agent.protocol_number_seq")
    assert sequence == [(number,)]
    interaction, last_value = (await bank.as_admin(INTERACTION_NUMBER, number=number))[0]
    assert interaction == last_value


async def test_the_protocol_row_seen_by_the_admin_oracle(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    number = await opened_number(app, STUDENT, PERSON)
    row = (await bank.as_admin(PROTOCOL_COLUMNS, number=number))[0]
    assert str(row[2]).startswith("SPA-")
    assert row[:2] == ("180017", "Student")
    assert row[3:] == (
        FREE_SERVICE,
        "Open",
        "Portal",
        "Normal",
        "False",
        OPENED_TEXT,
        DUE_TEXT,
        None,
        None,
        None,
        None,
    )


async def test_the_requester_is_written_with_the_cpf_and_name_of_the_person(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    number = await opened_number(app, STUDENT, PERSON)
    person = await bank.as_admin(PERSON_DATA, id=PERSON)
    assert await bank.as_admin(PROTOCOL_REQUESTER, number=number) == person


async def test_the_history_row_seen_by_the_admin_oracle(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    number = await opened_number(app, STUDENT, PERSON)
    assert await bank.as_admin(HISTORY, number=number) == [
        ("1", None, "Open", OPENED_TEXT, "system")
    ]


async def test_the_interaction_row_seen_by_the_admin_oracle(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    number = await opened_number(app, STUDENT, PERSON)
    full_name = (await bank.as_admin(PERSON_DATA, id=PERSON))[0][1]
    assert await bank.as_admin(INTERACTION, number=number) == [
        ("Requester", full_name, REQUEST_TEXT, "False", OPENED_TEXT)
    ]


async def test_only_the_three_tables_receive_writes(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    await opened_number(app, STUDENT, PERSON)
    assert await written_tables(bank) == {
        "secretary.protocol": ONE_INSERT,
        "secretary.protocol_status_history": ONE_INSERT,
        "secretary.protocol_interaction": ONE_INSERT,
    }


@pytest.mark.parametrize(
    ("student", "person"),
    [
        pytest.param(STUDENT, PERSON, id="in-person"),
        pytest.param(ONLINE_STUDENT, ONLINE_PERSON, id="online-with-a-leading-zero"),
    ],
)
async def test_the_new_protocol_appears_for_the_student(
    app: ConfirmationApp, student: str, person: str
) -> None:
    number = await opened_number(app, student, person)
    protocols = (await app.students().services_of(person)).protocol()
    listed = await protocols.list_protocols(None, None, None, FIRST_PAGE)
    detail = await protocols.get_protocol(number)
    assert number in {item.number for item in listed.data or []}
    assert detail.data is not None
    assert detail.data.protocol.enrollment == student


async def test_another_student_does_not_see_the_new_protocol(app: ConfirmationApp) -> None:
    number = await opened_number(app, STUDENT, PERSON)
    services = await app.students().services_of(ONLINE_PERSON)
    assert (await services.protocol().get_protocol(number)).data is None


async def test_the_token_of_another_student_is_not_found_and_writes_nothing(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    token = await app.proposal_of(PERSON, STUDENT)
    async with app.client() as client:
        response = await confirm(client, await login(client, OTHER_STUDENT), token)
    assert (response.status_code, response.text) == (HTTPStatus.NOT_FOUND, NOT_FOUND_BODY)
    assert await written_tables(bank) == {}


async def refused_tokens(app: ConfirmationApp, bank: RolledBackBank) -> tuple[str, ...]:
    token = await app.proposal_of(PERSON, STUDENT)
    expired_settings = app.settings.model_copy(update={"proposal_ttl_minutes": -1})
    expired = ConfirmationApp(bank.database, expired_settings)
    return (
        token[:-2] + ("AA" if token[-2:] != "AA" else "BB"),
        await expired.proposal_of(PERSON, STUDENT),
        "garbage",
        app.signer.sign(SignedProposal(PERSON, ONLINE_STUDENT, FREE_SERVICE)),
        app.signer.sign(SignedProposal(PERSON, STUDENT, "XXX-000")),
    )


async def test_every_refused_token_gets_the_same_404(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    tokens = await refused_tokens(app, bank)
    async with app.client() as client:
        owner = await login(client, STUDENT)
        refused = [await confirm(client, owner, item) for item in tokens]
    assert {response.status_code for response in refused} == {HTTPStatus.NOT_FOUND}
    assert {response.text for response in refused} == {NOT_FOUND_BODY}
    assert await written_tables(bank) == {}


async def test_the_second_confirmation_is_a_conflict(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    token = await app.proposal_of(PERSON, STUDENT)
    async with app.client() as client:
        headers = await login(client, STUDENT)
        first = await confirm(client, headers, token)
        second = await confirm(client, headers, token)
    assert (first.status_code, second.status_code) == (HTTPStatus.CREATED, HTTPStatus.CONFLICT)
    assert (await written_tables(bank))["secretary.protocol"] == ONE_INSERT


async def test_a_service_with_a_fee_is_unprocessable(
    app: ConfirmationApp, bank: RolledBackBank
) -> None:
    token = app.signer.sign(SignedProposal(PERSON, STUDENT, PAID_SERVICE))
    async with app.client() as client:
        response = await confirm(client, await login(client, STUDENT), token)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert await written_tables(bank) == {}


async def test_confirmation_without_identity_is_unauthorized(app: ConfirmationApp) -> None:
    token = await app.proposal_of(PERSON, STUDENT)
    async with app.client() as client:
        response = await confirm(client, {}, token)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

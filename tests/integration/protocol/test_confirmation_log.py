import io
import json
import logging
from collections.abc import AsyncIterator, Iterator

import pytest

from api.infrastructure.logging import JsonFormatter
from tests.integration.protocol.confirmation_app import ConfirmationApp, confirm, login
from tests.integration.protocol.information_request import REQUEST_TEXT
from tests.integration.protocol.rolled_back import RolledBackBank, rolled_back
from tests.integration.support.sql_oracle import admin_engine

STUDENT = "UniSaoPaulo:180017"
PERSON = "3000003"
FREE_SERVICE = "GEN-090"
PERSON_DATA = (
    r"SELECT regexp_replace(cpf, '\D', '', 'g'), full_name FROM sag.person WHERE person_id = :id"
)


@pytest.fixture
async def bank() -> AsyncIterator[RolledBackBank]:
    async with rolled_back(admin_engine(), "SET LOCAL ROLE api") as rolled:
        yield rolled


@pytest.fixture
def log_lines() -> Iterator[io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("api.application.protocol.confirmation")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield stream
    logger.removeHandler(handler)


async def confirm_one(bank: RolledBackBank) -> None:
    app = ConfirmationApp(bank.database)
    token = await app.proposal_of(PERSON, STUDENT)
    async with app.client() as client:
        await confirm(client, await login(client, STUDENT), token)


async def test_the_log_carries_the_trace_and_no_personal_data(
    bank: RolledBackBank, log_lines: io.StringIO
) -> None:
    await confirm_one(bank)
    written = log_lines.getvalue()
    entry = json.loads(written.splitlines()[0])
    assert entry["trace_id"]
    assert FREE_SERVICE in entry["message"]
    person = (await bank.as_admin(PERSON_DATA, id=PERSON))[0]
    for private in (*person, PERSON, STUDENT, REQUEST_TEXT):
        assert str(private) not in written

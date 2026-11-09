import pytest

from api.bootstrap.settings import Settings
from api.persistence.core.database import Database
from tests.integration.agent.agent_of import agent_for
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import student_tools
from tests.unit.agent.agent_support import tool_results

PERSON_OF_ENROLLMENT = (
    "SELECT person_id FROM sag.enrollment WHERE brand = :brand AND student_id = :student"
)


async def person_of_fi_01() -> str:
    people = await SqlOracle().values(
        PERSON_OF_ENROLLMENT, brand="UniAraucaria_EAD", student="013161"
    )
    return next(iter(people))


@pytest.mark.live
async def test_fi_01_calls_the_summary_and_answers_the_debt(database: Database) -> None:
    tools = await student_tools(database, await person_of_fi_01())
    agent = await agent_for(Settings.from_environment(), tools, "live-fi-01")

    run = await agent.run("Quanto estou devendo hoje?")

    used = [item.tool_name for item in tool_results(run.events)]
    assert "get_financial_summary" in used
    assert "277,05" in run.text


async def test_fi_01_with_the_scripted_model_reads_the_real_tool_output(database: Database) -> None:
    tools = await student_tools(database, await person_of_fi_01())
    settings = Settings.from_environment().model_copy(update={"agent_model": "fake"})
    agent = await agent_for(settings, tools, "fake-fi-01")

    run = await agent.run("Quanto estou devendo hoje?")

    result = tool_results(run.events)[0]
    assert (result.tool_name, result.status) == ("get_financial_summary", "ok")
    assert "277.05" in result.seen_by_model

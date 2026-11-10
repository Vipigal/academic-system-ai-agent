import pytest

from api.bootstrap.settings import Settings
from api.persistence.core.database import Database
from evals.graders.proposal import ProposalOutput
from tests.integration.agent.agent_of import agent_for
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import student_tools
from tests.unit.agent.agent_support import tool_results

BUG_REQUEST = "Solicite trancamento de matricula de Gestão Estratégica II"
LOCK_CODE = "ACA-010"
REPETITIONS = range(5)
PERSON_OF_ENROLLMENT = (
    "SELECT person_id FROM sag.enrollment WHERE brand = :brand AND student_id = :student"
)


async def person_of_the_anchor_student() -> str:
    people = await SqlOracle().values(PERSON_OF_ENROLLMENT, brand="UniMontanhas", student="070114")
    return next(iter(people))


@pytest.mark.live
@pytest.mark.parametrize("repetition", REPETITIONS)
async def test_a_subject_lock_request_never_yields_a_course_lock_proposal(
    database: Database, repetition: int
) -> None:
    tools = await student_tools(database, await person_of_the_anchor_student())
    agent = await agent_for(Settings.from_environment(), tools, f"live-subject-lock-{repetition}")

    run = await agent.run(BUG_REQUEST)

    accepted = [
        ProposalOutput.service_code(result.complete)
        for result in tool_results(run.events)
        if ProposalOutput.is_valid_proposal(result.tool_name, result.status)
    ]
    assert LOCK_CODE not in accepted

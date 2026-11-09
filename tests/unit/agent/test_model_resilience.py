import pytest

from api.application.agent.agent_errors import AgentFailedError
from tests.unit.agent import agent_support as support


async def test_a_transient_provider_failure_is_retried() -> None:
    run = await support.agent_with(support.FlakyModel(responses=[support.answer()])).run("Teste")

    assert run.text == support.FINAL_ANSWER


async def test_a_permanent_provider_failure_raises_an_application_error() -> None:
    model = support.FlakyModel(responses=[support.answer()], failures_left=10)

    with pytest.raises(AgentFailedError):
        await support.agent_with(model).run("Teste")

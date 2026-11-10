from dishka import AsyncContainer

from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.student_agent import StudentAgent
from tests.unit.agent.agent_support import tool_results
from tests.unit.agent.student_stubs import stub_student


async def test_the_fake_model_runs_the_same_script_for_every_request(
    dated_container: AsyncContainer,
) -> None:
    runtime = await dated_container.get(AgentRuntime)

    for trace_id in ("um", "dois"):
        agent = StudentAgent(runtime, stub_student().registry().tools, trace_id)
        run = await agent.run("Quanto devo?")
        assert [item.tool_name for item in tool_results(run.events)] == ["get_financial_summary"]
        assert run.text

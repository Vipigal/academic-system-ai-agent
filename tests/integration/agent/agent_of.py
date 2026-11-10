from langchain_core.language_models import BaseChatModel

from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.student_agent import StudentAgent
from api.application.agent.student_tools import StudentTools
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from evals.fixed_clock import FixedClock
from tests.doubles.doubles import DoubleContainers


async def agent_for(
    settings: Settings, tools: StudentTools, trace_id: str, model: BaseChatModel | None = None
) -> StudentAgent:
    doubles: dict[type, object] = {Clock: FixedClock()}
    if model is not None:
        doubles[BaseChatModel] = model
    container = DoubleContainers.students(settings, doubles)
    try:
        runtime = await container.get(AgentRuntime)
    finally:
        await container.close()
    return StudentAgent(runtime, tools.registry().tools, trace_id)

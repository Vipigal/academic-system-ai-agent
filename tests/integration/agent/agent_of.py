from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.student_agent import StudentAgent
from api.application.agent.student_tools import StudentTools
from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import FixedClock


async def agent_for(settings: Settings, tools: StudentTools, trace_id: str) -> StudentAgent:
    container = Containers.students(settings, {Clock: FixedClock()})
    try:
        runtime = await container.get(AgentRuntime)
    finally:
        await container.close()
    return StudentAgent(runtime, tools.registry().tools, trace_id)

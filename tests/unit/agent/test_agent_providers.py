from dishka import AsyncContainer
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.scripted_model import ScriptedChatModel
from api.application.agent.student_agent import StudentAgent
from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import FixedClock, SystemClock
from tests.unit.agent.agent_support import tool_results
from tests.unit.agent.student_stubs import stub_student

DATABASE_URL = "postgresql+asyncpg://api:api@127.0.0.1:5432/nada"


def settings_with(**values: object) -> Settings:
    return Settings.model_validate({"database_url": DATABASE_URL, **values})


async def test_the_real_model_uses_the_responses_api_with_the_configured_effort() -> None:
    settings = settings_with(agent_model="gpt-6-luna", agent_effort="medium", OPENAI_API_KEY="k")

    container = Containers.http(settings)
    try:
        model = await container.get(BaseChatModel)
    finally:
        await container.close()

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-6-luna"
    assert model.use_responses_api is True
    assert model.reasoning_effort == "medium"
    assert model.max_retries == 0


async def test_the_fake_model_is_chosen_by_configuration() -> None:
    container = Containers.http(settings_with(agent_model="fake"))
    try:
        assert isinstance(await container.get(BaseChatModel), ScriptedChatModel)
    finally:
        await container.close()


async def test_limits_come_from_the_settings() -> None:
    settings = settings_with(
        agent_model="fake",
        agent_model_call_limit=3,
        agent_tool_call_limit=4,
        agent_timeout_seconds=5,
    )

    container = Containers.http(settings, {Clock: FixedClock()})
    try:
        limits = (await container.get(AgentRuntime)).limits
    finally:
        await container.close()

    assert limits.model_calls == 3
    assert limits.tool_calls == 4
    assert limits.timeout_seconds == 5


async def test_singletons_start_without_a_key_and_build_the_model_once() -> None:
    container = Containers.http(settings_with(agent_model="fake"))

    assert await container.get(AgentRuntime) is await container.get(AgentRuntime)
    await container.close()


async def test_singletons_use_the_system_clock_unless_another_is_given() -> None:
    production = Containers.http(settings_with(agent_model="fake"))
    injected = Containers.http(settings_with(agent_model="fake"), {Clock: FixedClock()})

    assert isinstance(await production.get(Clock), SystemClock)
    assert "Hoje é 31/10/2026." in (await injected.get(AgentRuntime)).system_message()
    await production.close()
    await injected.close()


async def test_the_fake_model_runs_the_same_script_for_every_request(
    dated_container: AsyncContainer,
) -> None:
    runtime = await dated_container.get(AgentRuntime)

    for trace_id in ("um", "dois"):
        agent = StudentAgent(runtime, stub_student().registry().tools, trace_id)
        run = await agent.run("Quanto devo?")
        assert [item.tool_name for item in tool_results(run.events)] == ["get_financial_summary"]
        assert run.text

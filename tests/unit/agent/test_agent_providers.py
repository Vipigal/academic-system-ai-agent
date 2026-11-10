from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from api.application.agent.agent_runtime import AgentRuntime
from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import SystemClock
from evals.fixed_clock import FixedClock
from tests.doubles.doubles import DoubleContainers
from tests.doubles.scripted_model import ScriptedChatModel

SCRIPTED = ScriptedChatModel.standard()
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


async def test_limits_come_from_the_settings() -> None:
    settings = settings_with(
        agent_model_call_limit=3,
        agent_tool_call_limit=4,
        agent_timeout_seconds=5,
    )

    container = DoubleContainers.http(settings, {Clock: FixedClock(), BaseChatModel: SCRIPTED})
    try:
        limits = (await container.get(AgentRuntime)).limits
    finally:
        await container.close()

    assert limits.model_calls == 3
    assert limits.tool_calls == 4
    assert limits.timeout_seconds == 5


async def test_singletons_build_the_model_once() -> None:
    container = Containers.http(settings_with(OPENAI_API_KEY="k"))

    assert await container.get(AgentRuntime) is await container.get(AgentRuntime)
    await container.close()


async def test_singletons_use_the_system_clock_unless_another_is_given() -> None:
    production = Containers.http(settings_with())
    injected = DoubleContainers.http(
        settings_with(), {Clock: FixedClock(), BaseChatModel: SCRIPTED}
    )

    assert isinstance(await production.get(Clock), SystemClock)
    assert "Hoje é 31/10/2026." in (await injected.get(AgentRuntime)).system_message()
    await production.close()
    await injected.close()

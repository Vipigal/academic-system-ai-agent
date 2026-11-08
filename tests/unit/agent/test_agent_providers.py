from langchain_openai import ChatOpenAI

from api.application.agent.scripted_model import ScriptedChatModel
from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.infrastructure.clock import FixedClock, SystemClock
from tests.unit.agent.agent_support import tool_results
from tests.unit.agent.student_stubs import stub_student

DATABASE_URL = "postgresql+asyncpg://api:api@127.0.0.1:5432/nada"


def settings_with(**values: object) -> Settings:
    return Settings.model_validate({"database_url": DATABASE_URL, **values})


def test_the_real_model_uses_the_responses_api_with_the_configured_effort() -> None:
    settings = settings_with(agent_model="gpt-6-luna", agent_effort="medium", OPENAI_API_KEY="k")

    model = AgentProviders.chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-6-luna"
    assert model.use_responses_api is True
    assert model.reasoning_effort == "medium"
    assert model.max_retries == 0


def test_the_fake_model_is_chosen_by_configuration() -> None:
    assert isinstance(
        AgentProviders.chat_model(settings_with(agent_model="fake")), ScriptedChatModel
    )


def test_limits_come_from_the_settings() -> None:
    settings = settings_with(
        agent_model="fake",
        agent_model_call_limit=3,
        agent_tool_call_limit=4,
        agent_timeout_seconds=5,
    )

    limits = AgentProviders(settings, FixedClock()).runtime.limits

    assert limits.model_calls == 3
    assert limits.tool_calls == 4
    assert limits.timeout_seconds == 5


async def test_singletons_start_without_a_key_and_build_the_model_once() -> None:
    singletons = Singletons.create(settings_with(agent_model="fake"))

    assert singletons.agent.runtime is singletons.agent.runtime
    await singletons.dispose()


async def test_singletons_use_the_system_clock_unless_another_is_given() -> None:
    production = Singletons.create(settings_with(agent_model="fake"))
    injected = Singletons.create(settings_with(agent_model="fake"), FixedClock())

    assert isinstance(production.clock, SystemClock)
    assert "Hoje é 31/10/2026." in injected.agent.runtime.system_message()
    await production.dispose()
    await injected.dispose()


async def test_the_fake_model_runs_the_same_script_for_every_request() -> None:
    providers = AgentProviders(settings_with(agent_model="fake"), FixedClock())

    for trace_id in ("um", "dois"):
        run = await providers.agent_for(stub_student(), trace_id).run("Quanto devo?")
        assert [item.tool_name for item in tool_results(run.events)] == ["get_financial_summary"]
        assert run.text

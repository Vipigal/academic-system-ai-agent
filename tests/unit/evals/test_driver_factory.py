from datetime import date

from api.application.agent.agent_runtime import AgentRuntime
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from evals.eval_container import EvalContainer

SETTINGS = Settings.model_validate(
    {"database_url": "postgresql+asyncpg://api:api@127.0.0.1:5432/nada", "OPENAI_API_KEY": "k"}
)


async def test_the_eval_builds_the_agent_on_the_day_of_the_data_snapshot() -> None:
    container = EvalContainer.create(SETTINGS)

    assert (await container.get(Clock)).today() == date(2026, 10, 31)
    assert "Hoje é 31/10/2026." in (await container.get(AgentRuntime)).system_message()
    await container.close()

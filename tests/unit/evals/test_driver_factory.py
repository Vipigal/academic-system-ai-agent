from datetime import date

from api.bootstrap.settings import Settings
from evals.driver_factory import DriverFactory

SETTINGS = Settings.model_validate(
    {"database_url": "postgresql+asyncpg://api:api@127.0.0.1:5432/nada", "agent_model": "fake"}
)


async def test_the_eval_builds_the_agent_on_the_day_of_the_data_snapshot() -> None:
    singletons = DriverFactory.singletons_for(SETTINGS)

    assert singletons.clock.today() == date(2026, 10, 31)
    assert "Hoje é 31/10/2026." in singletons.agent.runtime.system_message()
    await singletons.dispose()

from langfuse import observe

from api.application.health.dto.check import HealthDto
from api.domain.ports.health import DatabaseProbe


class HealthService:
    def __init__(self, database: DatabaseProbe) -> None:
        self._database = database

    @observe(name="health.check", capture_input=False, capture_output=False)
    async def check(self) -> HealthDto:
        return HealthDto(database_available=await self._database.is_available())

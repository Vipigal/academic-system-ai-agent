from api.application.dto.health_dto import HealthDto
from api.domain.ports import DatabaseProbe


class HealthService:
    def __init__(self, database: DatabaseProbe) -> None:
        self._database = database

    async def check(self) -> HealthDto:
        return HealthDto(database_available=await self._database.is_available())

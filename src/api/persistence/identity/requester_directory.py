from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.requester_queries import REQUESTER_NAMES


class SqlRequesterDirectory:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def full_name_of(self, person_id: str) -> str | None:
        rows = await self._adapter.fetch_declared(REQUESTER_NAMES)
        return next((name for found, name in rows if found == person_id), None)

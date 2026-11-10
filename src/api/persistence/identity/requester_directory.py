from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.requester_queries import RequesterQueries


class SqlRequesterDirectory:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def full_name_of(self, person_id: str) -> str | None:
        rows = await self._adapter.fetch_rows(RequesterQueries.names_of_the_session())
        return next((name for found, name in rows if found == person_id), None)

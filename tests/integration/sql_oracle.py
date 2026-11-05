from sqlalchemy import text

from api.persistence.database import Database


class SqlOracle:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def values(self, sql: str, **parameters: str) -> set[str]:
        async with self._database.db_session_factory() as db:
            result = await db.execute(text(sql), parameters)
            return {str(row[0]) for row in result}

    async def count(self, sql: str, **parameters: str) -> int:
        return int(next(iter(await self.values(sql, **parameters))))

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_sessionmaker

from api.persistence.core.database import Database
from tests.integration.support.sql_oracle import admin_url

ROLE_API = text("SET LOCAL ROLE api")
ADMIN = text("RESET ROLE")

type AdminRow = tuple[str | None, ...]


class RolledBackBank:
    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection
        self.database = Database(admin_url())
        self.database.db_session_factory = async_sessionmaker(
            bind=connection, expire_on_commit=False, join_transaction_mode="rollback_only"
        )

    async def as_admin(self, sql: str, **parameters: str) -> list[AdminRow]:
        await self._connection.execute(ADMIN)
        result = await self._connection.execute(text(sql), parameters)
        rows = [tuple(row) for row in result.all()]
        await self._connection.execute(ROLE_API)
        return rows

    async def as_app(self, sql: str) -> str:
        return str(await self._connection.scalar(text(sql)))


@asynccontextmanager
async def rolled_back(engine: AsyncEngine, statement: str) -> AsyncGenerator[RolledBackBank]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(text(statement))
        try:
            yield RolledBackBank(connection)
        finally:
            await transaction.rollback()

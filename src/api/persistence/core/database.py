from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

CONNECT_TIMEOUT_SECONDS = 5


class Database:
    def __init__(self, url: str) -> None:
        self._engine = create_async_engine(
            url, connect_args={"timeout": CONNECT_TIMEOUT_SECONDS}, hide_parameters=True
        )
        self.db_session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def is_available(self) -> bool:
        try:
            async with self.db_session_factory() as db:
                await db.execute(select(1))
        except SQLAlchemyError, OSError:
            return False
        return True

    async def dispose(self) -> None:
        await self._engine.dispose()

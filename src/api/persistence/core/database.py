from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

CONNECT_TIMEOUT_SECONDS = 5


@dataclass(frozen=True, slots=True)
class PoolConfig:
    size: int
    max_overflow: int
    timeout_seconds: float

    def engine_options(self) -> dict[str, float | bool]:
        return {
            "pool_size": self.size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.timeout_seconds,
            "pool_pre_ping": True,
        }


class Database:
    def __init__(self, url: str, pool: PoolConfig | None = None) -> None:
        options = pool.engine_options() if pool else {}
        self._engine = create_async_engine(
            url,
            connect_args={"timeout": CONNECT_TIMEOUT_SECONDS},
            hide_parameters=True,
            **options,
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

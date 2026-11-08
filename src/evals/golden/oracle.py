import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import TracebackType
from typing import Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from evals.golden.oracle_queries import ORACLE_QUERIES
from evals.golden.oracle_queries.scope import STUDENT_SCOPE

NAMED_PARAMETER = re.compile(r"(?<![:\w]):([a-z_]+)\b")
STUDENT_PARAMETER = "student"


class OracleQueryError(RuntimeError):
    pass


class OracleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    oracle_database_url: SecretStr

    @classmethod
    def from_environment(cls) -> Self:
        return cls.model_validate(EnvSettingsSource(cls)())


@dataclass(frozen=True, slots=True)
class PreparedQuery:
    sql: str
    arguments: tuple[str, ...]


class QueryPreparer:
    @staticmethod
    def parameters_of(query_name: str) -> frozenset[str]:
        return frozenset(NAMED_PARAMETER.findall(ORACLE_QUERIES[query_name])) - {STUDENT_PARAMETER}

    @staticmethod
    def prepare(query_name: str, student: str, params: Mapping[str, str]) -> PreparedQuery:
        values = {STUDENT_PARAMETER: student, **params}
        names = list(values)

        def positional(found: re.Match[str]) -> str:
            position = names.index(found.group(1)) + 1
            return f"${position}"

        sql = f"{STUDENT_SCOPE}{ORACLE_QUERIES[query_name]}"
        return PreparedQuery(NAMED_PARAMETER.sub(positional, sql), tuple(values.values()))


class Oracle:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, poolclass=NullPool)
        self._connection: AsyncConnection | None = None

    @classmethod
    def from_environment(cls) -> Self:
        settings = OracleSettings.from_environment()
        return cls(settings.oracle_database_url.get_secret_value())

    async def __aenter__(self) -> Self:
        self._connection = await self._engine.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._connection is not None:
            await self._connection.close()
        await self._engine.dispose()

    async def rows(
        self, query_name: str, student: str, params: Mapping[str, str]
    ) -> list[str | None]:
        if self._connection is None:
            raise RuntimeError("Abra o oráculo com async with antes de consultar")
        prepared = QueryPreparer.prepare(query_name, student, params)
        try:
            result = await self._connection.exec_driver_sql(prepared.sql, prepared.arguments)
        except DBAPIError as error:
            await self._connection.rollback()
            raise OracleQueryError(f"{query_name} falhou: {error.orig}") from error
        return [self._cell(row[0]) for row in result]

    @staticmethod
    def _cell(value: object) -> str | None:
        return None if value is None else str(value)

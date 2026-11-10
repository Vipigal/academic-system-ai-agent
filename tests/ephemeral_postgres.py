import asyncio
import os
import time
from pathlib import Path

from docker.errors import DockerException
from sqlalchemy import URL, make_url, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.core.container import DockerContainer
from testcontainers.core.docker_client import DockerClient
from testcontainers.core.wait_strategies import ExecWaitStrategy

ROOT = Path(__file__).parent.parent
IMAGE = "postgres:18.6-trixie"
PORT = 5432
TEMPLATE = "cruzeiro"
ADMIN = "postgres"
APPLICATION = "api"
MAINTENANCE = "postgres"
STARTUP_SECONDS = 180
SERVER_VARIABLE = "TESTS_DATABASE_SERVER"
UNREACHABLE = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nothing"
LOADED = (
    "psql",
    "--host",
    "127.0.0.1",
    "--username",
    ADMIN,
    "--dbname",
    TEMPLATE,
    "--command",
    f"SET ROLE {APPLICATION}",
)


def docker_answers() -> bool:
    try:
        client = DockerClient()
    except DockerException:
        return False
    client.client.close()
    return True


class EphemeralPostgres:
    def __init__(self) -> None:
        self.load_seconds = 0.0
        self._container = (
            DockerContainer(IMAGE)
            .with_envs(
                POSTGRES_USER=ADMIN,
                POSTGRES_PASSWORD=ADMIN,
                POSTGRES_DB=TEMPLATE,
                API_DB_PASSWORD=APPLICATION,
            )
            .with_volume_mapping(ROOT / "data", "/data", "ro")
            .with_volume_mapping(ROOT / "db" / "init", "/docker-entrypoint-initdb.d", "ro")
            .with_exposed_ports(PORT)
            .waiting_for(ExecWaitStrategy(list(LOADED)).with_startup_timeout(STARTUP_SECONDS))
        )

    def start(self) -> str:
        started = time.monotonic()
        self._container.start()
        self.load_seconds = time.monotonic() - started
        server = URL.create(
            "postgresql+asyncpg",
            username=ADMIN,
            password=ADMIN,
            host=self._container.get_container_host_ip(),
            port=self._container.get_exposed_port(PORT),
            database=TEMPLATE,
        )
        return server.render_as_string(hide_password=False)

    def stop(self) -> None:
        self._container.stop()


def clone_template(server: str, name: str) -> str:
    asyncio.run(_create_from_template(server, name))
    return name


async def _create_from_template(server: str, name: str) -> None:
    maintenance = make_url(server).set(database=MAINTENANCE)
    engine = create_async_engine(maintenance, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with engine.connect() as connection:
        for statement in (
            f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)',
            f'CREATE DATABASE "{name}" TEMPLATE {TEMPLATE}',
            f'REVOKE ALL ON DATABASE "{name}" FROM PUBLIC',
            f'GRANT CONNECT ON DATABASE "{name}" TO {APPLICATION}',
        ):
            await connection.execute(text(statement))
    await engine.dispose()


def point_environment(server: str, database: str) -> None:
    if not server:
        os.environ["APP_ORACLE_DATABASE_URL"] = UNREACHABLE
        os.environ["APP_DATABASE_URL"] = UNREACHABLE
        return
    admin = make_url(server).set(database=database)
    application = admin.set(username=APPLICATION, password=APPLICATION)
    os.environ["APP_ORACLE_DATABASE_URL"] = admin.render_as_string(hide_password=False)
    os.environ["APP_DATABASE_URL"] = application.render_as_string(hide_password=False)

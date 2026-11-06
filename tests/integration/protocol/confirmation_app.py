import secrets

import httpx
from fastapi import FastAPI
from pydantic import SecretStr

from api.bootstrap.identity_providers import IdentityProviders
from api.bootstrap.protocol_confirmation_assembly import ProtocolConfirmationAssembly
from api.bootstrap.protocol_confirmation_providers import ProtocolConfirmationProviders
from api.bootstrap.protocol_providers import ProtocolProviders
from api.bootstrap.settings import Settings
from api.bootstrap.student_providers import StudentProviders
from api.persistence.core.database import Database
from tests.integration.support.tools import FixedClock

JWT_SECRET = secrets.token_urlsafe(32)
PROPOSAL_SECRET = secrets.token_urlsafe(32)
REQUEST_MESSAGE = "Pedido do aluno"


def settings_with(**overrides: object) -> Settings:
    updates = {
        "jwt_secret": SecretStr(JWT_SECRET),
        "proposal_secret": SecretStr(PROPOSAL_SECRET),
        "dev_login": True,
        **overrides,
    }
    return Settings.from_environment().model_copy(update=updates)


class ConfirmationApp:
    def __init__(self, database: Database, settings: Settings | None = None) -> None:
        self.settings = settings or settings_with()
        self.signer = ProtocolProviders.signer_of(self.settings)
        self._database = database
        self._application = FastAPI()
        self._mount(IdentityProviders(self.settings, database))

    def _mount(self, identity: IdentityProviders) -> None:
        assembly = ProtocolConfirmationAssembly(self._database, FixedClock(), self.signer)
        confirmation = ProtocolConfirmationProviders(assembly, identity.session_dependency())
        login_router = identity.auth_router()
        if login_router is not None:
            self._application.include_router(login_router)
        self._application.include_router(confirmation.router())

    def client(self) -> httpx.AsyncClient:
        transport = httpx.ASGITransport(app=self._application)
        return httpx.AsyncClient(transport=transport, base_url="http://api")

    def students(self) -> StudentProviders:
        return StudentProviders(self._database, FixedClock(), self.signer)

    async def proposal_of(self, person_id: str, service: str) -> str:
        services = await self.students().services_of(person_id)
        result = await services.protocol().propose_protocol(service, None, REQUEST_MESSAGE)
        assert result.client_only is not None
        return result.client_only["token"]


async def login(client: httpx.AsyncClient, student: str) -> dict[str, str]:
    response = await client.post("/auth/dev-login", json={"student": student})
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def confirm(client: httpx.AsyncClient, headers: dict[str, str], token: str) -> httpx.Response:
    return await client.post("/protocols/proposals/confirm", json={"token": token}, headers=headers)

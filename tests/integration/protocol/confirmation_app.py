import httpx
from fastapi import FastAPI

from api.bootstrap.identity_providers import IdentityProviders
from api.bootstrap.protocol_confirmation_assembly import ProtocolConfirmationAssembly
from api.bootstrap.protocol_confirmation_providers import ProtocolConfirmationProviders
from api.bootstrap.protocol_providers import ProtocolProviders
from api.bootstrap.settings import Settings
from api.bootstrap.student_providers import StudentProviders
from api.infrastructure.clock import FixedClock
from api.persistence.core.database import Database
from tests.integration.protocol.confirmation_settings import settings_with
from tests.integration.protocol.information_request import (
    WRITTEN,
    conversation_for,
    information_token,
)


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

    async def proposal_of(self, person_id: str, enrollment: str) -> str:
        return await information_token(self.students(), person_id, enrollment)

    async def conversation_of(self, person_id: str) -> str:
        return await conversation_for(self._database, person_id)

    async def confirmed_by(
        self, student: str, person_id: str, token: str, answer: dict[str, str] | None = None
    ) -> tuple[httpx.Response, str]:
        conversation = await self.conversation_of(person_id)
        async with self.client() as client:
            headers = await login(client, student)
            return await confirm(client, headers, token, conversation, answer), conversation


async def login(client: httpx.AsyncClient, student: str) -> dict[str, str]:
    response = await client.post("/auth/dev-login", json={"student": student})
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def confirm(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    token: str,
    conversation: str,
    answer: dict[str, str] | None = None,
) -> httpx.Response:
    body = {"token": token, "conversation_id": conversation, **(answer or {})}
    return await client.post("/protocols/proposals/confirm", json=body, headers=headers)


async def confirmed_on(
    app: ConfirmationApp, student: str, token: str, conversations: tuple[str, ...]
) -> list[httpx.Response]:
    async with app.client() as client:
        headers = await login(client, student)
        return [
            await confirm(client, headers, token, conversation, WRITTEN)
            for conversation in conversations
        ]

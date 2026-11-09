import httpx
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from api.application.protocol.service import ProtocolService
from api.bootstrap.routes import ApiRoutes
from api.bootstrap.settings import Settings
from api.domain.ports.protocol import ProposalSigner
from api.persistence.core.database import Database
from tests.integration.protocol.confirmation_container import confirmation_container
from tests.integration.protocol.confirmation_settings import settings_with
from tests.integration.protocol.information_request import (
    WRITTEN,
    conversation_for,
    information_token,
)
from tests.integration.support.student_scopes import StudentScopes


class ConfirmationApp:
    def __init__(self, database: Database, settings: Settings | None = None) -> None:
        self.settings = settings or settings_with()
        container = confirmation_container(database, self.settings)
        self.signer: ProposalSigner = container.get_sync(ProposalSigner)
        self._database = database
        self._application = FastAPI()
        ApiRoutes.mount(self._application, self.settings)
        setup_dishka(container, self._application)

    def client(self) -> httpx.AsyncClient:
        transport = httpx.ASGITransport(app=self._application)
        return httpx.AsyncClient(transport=transport, base_url="http://api")

    def students(self) -> StudentScopes:
        return StudentScopes(self._database, self.signer)

    async def protocols_of(self, person_id: str) -> ProtocolService:
        return await self.students().of_person(person_id, ProtocolService)

    async def proposal_of(self, person_id: str, enrollment: str) -> str:
        return await information_token(await self.protocols_of(person_id), enrollment)

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

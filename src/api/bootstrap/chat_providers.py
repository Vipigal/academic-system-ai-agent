from functools import partial
from typing import Annotated

from fastapi import APIRouter, Depends

from api.application.chat.service import ChatService
from api.application.chat.turn_input import ChatOptions
from api.bootstrap.chat_agent_scope import ChatAgentScope
from api.bootstrap.history_providers import HistoryProviders
from api.bootstrap.identity_providers import IdentityProviders
from api.bootstrap.singletons import Singletons
from api.domain.identity.session import StudentSession
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.presentation.http.chat import ChatRouter


class ChatProviders:
    def __init__(
        self, singletons: Singletons, agent_scope: ChatAgentScope, identity: IdentityProviders
    ) -> None:
        self._singletons = singletons
        self._agent_scope = agent_scope
        self._identity = identity

    def router(self) -> APIRouter:
        session_dependency = self._identity.session_dependency()

        async def chat_service(
            session: Annotated[StudentSession, Depends(session_dependency)],
            person_id: Annotated[str, Depends(self._identity.person_id)],
        ) -> ChatService:
            return self.service_for(session, person_id)

        return ChatRouter.build(chat_service)

    def service_for(self, session: StudentSession, person_id: str) -> ChatService:
        settings = self._singletons.settings
        adapter = RepositoryAdapter(self._singletons.database.db_session_factory, session)
        return ChatService(
            HistoryProviders(adapter).conversations(),
            partial(self._agent_scope.traced_agent, session, person_id),
            ChatOptions(person_id, settings.history_window, settings.agent_model),
        )

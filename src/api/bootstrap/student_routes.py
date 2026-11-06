from fastapi import FastAPI

from api.bootstrap.chat_agent_scope import ChatAgentScope
from api.bootstrap.chat_providers import ChatProviders
from api.bootstrap.identity_providers import IdentityProviders
from api.bootstrap.protocol_confirmation_assembly import ProtocolConfirmationAssembly
from api.bootstrap.protocol_confirmation_providers import ProtocolConfirmationProviders
from api.bootstrap.protocol_providers import ProtocolProviders
from api.bootstrap.singletons import Singletons
from api.infrastructure.tracing import CurrentTrace, Tracing


class StudentRoutes:
    def __init__(self, singletons: Singletons, tracing: Tracing) -> None:
        self._singletons = singletons
        self._tracing = tracing
        self._identity = IdentityProviders(singletons.settings, singletons.database)

    def mount(self, application: FastAPI) -> None:
        login = self._identity.auth_router()
        if login is not None:
            application.include_router(login)
        scope = ChatAgentScope(self._singletons, self._tracing)
        chat = ChatProviders(self._singletons, scope, self._identity)
        application.include_router(chat.router())
        application.include_router(self._confirmation().router())

    def _confirmation(self) -> ProtocolConfirmationProviders:
        assembly = ProtocolConfirmationAssembly(
            self._singletons.database,
            self._singletons.clock,
            ProtocolProviders.signer_of(self._singletons.settings),
            CurrentTrace(enabled=self._tracing.enabled),
        )
        return ProtocolConfirmationProviders(assembly, self._identity.session_dependency())

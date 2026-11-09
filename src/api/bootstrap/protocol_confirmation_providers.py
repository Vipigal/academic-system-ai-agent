from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends

from api.application.protocol.confirmation import ProtocolConfirmation
from api.bootstrap.protocol_confirmation_assembly import ProtocolConfirmationAssembly
from api.domain.identity.session import StudentSession
from api.presentation.http.protocol_confirmation import ProtocolConfirmationRouter


class ProtocolConfirmationProviders:
    def __init__(
        self,
        assembly: ProtocolConfirmationAssembly,
        session_dependency: Callable[..., Awaitable[StudentSession]],
    ) -> None:
        self._assembly = assembly
        self._session_dependency = session_dependency

    def router(self) -> APIRouter:
        async def confirmation(
            session: Annotated[StudentSession, Depends(self._session_dependency)],
        ) -> ProtocolConfirmation:
            return self._assembly.for_session(session)

        return ProtocolConfirmationRouter.build(confirmation)

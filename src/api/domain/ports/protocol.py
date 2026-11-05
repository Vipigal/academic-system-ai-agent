from collections.abc import Sequence
from typing import Protocol

from api.domain.protocol import Protocol as StudentProtocol
from api.domain.protocol_catalog import Service


class ProtocolRepository(Protocol):
    async def list_services(self) -> Sequence[Service]: ...

    async def list_protocols(self) -> Sequence[StudentProtocol]: ...

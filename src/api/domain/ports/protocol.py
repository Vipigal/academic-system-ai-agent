from collections.abc import Sequence
from typing import Protocol

from api.domain.protocol.catalog import Service
from api.domain.protocol.request import Protocol as StudentProtocol


class ProtocolRepository(Protocol):
    async def list_services(self) -> Sequence[Service]: ...

    async def list_protocols(self) -> Sequence[StudentProtocol]: ...

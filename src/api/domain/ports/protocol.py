from collections.abc import Sequence
from typing import Protocol

from api.domain.protocol.catalog import Service
from api.domain.protocol.opening import ProtocolOpening
from api.domain.protocol.proposal import SignedProposal
from api.domain.protocol.request import Protocol as StudentProtocol


class ProtocolRepository(Protocol):
    async def list_services(self) -> Sequence[Service]: ...

    async def list_protocols(self) -> Sequence[StudentProtocol]: ...


class ProtocolWriter(Protocol):
    async def save(self, opening: ProtocolOpening) -> str: ...


class ProposalSigner(Protocol):
    def sign(self, proposal: SignedProposal) -> str: ...

    def verify(self, token: str) -> SignedProposal | None: ...

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from uuid import UUID, uuid4

from api.application.protocol.confirmation import ProtocolConfirmation
from api.application.protocol.confirmation_ports import ConfirmationPorts
from api.domain.conversation.errors import ConversationConflictError, ConversationNotFoundError
from api.domain.conversation.message import Message
from api.domain.protocol.opening import ProtocolOpening
from api.domain.protocol.proposal import SignedProposal
from api.domain.shared.money import Money
from evals.fixed_clock import FixedClock
from tests.unit.protocol import proposal_fakes as fakes

NUMBER = "20260025165"
REQUESTER = "Maria Souza"
CONVERSATION = uuid4()
DECLARATION = replace(fakes.LOCK, code="DOC-001", name="Enrollment Certificate", sla_hours=48)
REACTIVATION = replace(fakes.LOCK, code="ACA-011", name="Enrollment Reactivation")
TRANSCRIPT = replace(fakes.LOCK, code="DOC-002", name="Printed Transcript")
PAID_SLIP = replace(fakes.LOCK, code="FIN-030", name="Payment Slip", fee=Money(10))
SERVICES = (*fakes.FakeProtocols().services, DECLARATION, REACTIVATION, TRANSCRIPT, PAID_SLIP)


@dataclass
class TokenSigner:
    proposals: dict[str, SignedProposal] = field(default_factory=dict)

    def sign(self, proposal: SignedProposal) -> str:
        token = f"{proposal.person_id}:{proposal.service_code}:{proposal.enrollment}"
        self.proposals[token] = proposal
        return token

    def verify(self, token: str) -> SignedProposal | None:
        return self.proposals.get(token)


class NamedRequesters:
    async def full_name_of(self, person_id: str) -> str | None:
        return REQUESTER if person_id == fakes.PERSON else None


@dataclass
class RecordingWriter:
    saved: list[ProtocolOpening] = field(default_factory=list)

    async def save(self, opening: ProtocolOpening) -> str:
        self.saved.append(opening)
        return NUMBER


@dataclass
class FakeConversations:
    conflicts: int = 0
    broken: bool = False
    appended: list[Message] = field(default_factory=list)

    async def create(self, person_id: str) -> UUID:
        return CONVERSATION if person_id == fakes.PERSON else uuid4()

    async def require(self, conversation_id: UUID) -> None:
        if conversation_id != CONVERSATION:
            raise ConversationNotFoundError

    async def append(self, conversation_id: UUID, messages: Sequence[Message]) -> None:
        await self.require(conversation_id)
        if self.broken:
            raise ConnectionError
        if self.conflicts:
            self.conflicts -= 1
            raise ConversationConflictError
        self.appended.extend(messages)

    async def window(self, conversation_id: UUID, limit: int) -> Sequence[Message]:
        await self.require(conversation_id)
        return self.appended[-limit:]


class SilentTrace:
    def bind_to_log(self) -> None:
        return None


@dataclass
class ConfirmationBench:
    signer: TokenSigner = field(default_factory=TokenSigner)
    writer: RecordingWriter = field(default_factory=RecordingWriter)
    conversations: FakeConversations = field(default_factory=FakeConversations)

    def token_for(self, service_code: str, enrollment: str = fakes.ACTIVE.reference) -> str:
        return self.signer.sign(SignedProposal(fakes.PERSON, enrollment, service_code))

    def confirmation(self) -> ProtocolConfirmation:
        ports = ConfirmationPorts(
            signer=self.signer,
            protocols=fakes.FakeProtocols(services=SERVICES),
            academic=fakes.FakeAcademic(),
            requesters=NamedRequesters(),
            writer=self.writer,
            conversations=self.conversations,
        )
        return ProtocolConfirmation(fakes.SESSION, ports, FixedClock(), SilentTrace())

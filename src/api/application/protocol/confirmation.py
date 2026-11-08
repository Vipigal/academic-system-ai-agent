import logging

from langfuse import observe

from api.application.protocol.confirmation_event import ConfirmationEvent, ConversationEvents
from api.application.protocol.confirmation_ports import ConfirmationPorts, OpeningParties
from api.application.protocol.dto.confirmation import ConfirmedProtocolDto
from api.application.protocol.proposal_parties import ProposalParties
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.tracing import TraceLog
from api.domain.protocol.errors import ProposalNotFoundError
from api.domain.protocol.opening import OpeningRequest, ProtocolOpening, StudentAnswer

logger = logging.getLogger(__name__)


class ProtocolConfirmation:
    def __init__(
        self, session: StudentSession, ports: ConfirmationPorts, clock: Clock, trace: TraceLog
    ) -> None:
        self._session = session
        self._ports = ports
        self._clock = clock
        self._trace = trace
        self._parties = ProposalParties(ports)
        self._events = ConversationEvents(ports.conversations)

    @observe(name="protocol.confirm", capture_input=False, capture_output=False)
    async def confirm(
        self, token: str, conversation_id: str, answer: StudentAnswer
    ) -> ConfirmedProtocolDto:
        self._trace.bind_to_log()
        proposal = self._ports.signer.verify(token)
        if proposal is None or proposal.person_id not in self._session.person_ids:
            raise ProposalNotFoundError
        conversation = await self._events.conversation_of(conversation_id)
        parties = await self._parties.of(proposal)
        opening = await self._opening_of(parties, answer)
        number = await self._ports.writer.save(opening)
        logger.info("Protocolo confirmado: serviço %s", opening.service_code)
        await self._events.attach(conversation, ConfirmationEvent.message(number, opening, parties))
        return ConfirmedProtocolDto.of(number, opening)

    async def _opening_of(self, parties: OpeningParties, answer: StudentAnswer) -> ProtocolOpening:
        existing = await self._ports.protocols.list_protocols()
        request = OpeningRequest(
            parties.requester_name, parties.action, answer, self._clock.today()
        )
        return ProtocolOpening.open(parties.service, parties.enrollment, existing, request)

import asyncio
import logging

from langfuse import observe

from api.application.protocol.confirmation_ports import ConfirmationPorts, OpeningParties
from api.application.protocol.dto.confirmation import ConfirmedProtocolDto
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.tracing import TraceLog
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.errors import ProposalNotFoundError
from api.domain.protocol.opening import OpeningRequest, ProtocolOpening
from api.domain.protocol.proposal import SignedProposal

logger = logging.getLogger(__name__)


class ProtocolConfirmation:
    def __init__(
        self, session: StudentSession, ports: ConfirmationPorts, clock: Clock, trace: TraceLog
    ) -> None:
        self._session = session
        self._ports = ports
        self._clock = clock
        self._trace = trace

    @observe(name="protocol.confirm", capture_input=False, capture_output=False)
    async def confirm(self, token: str) -> ConfirmedProtocolDto:
        self._trace.bind_to_log()
        proposal = self._ports.signer.verify(token)
        if proposal is None or proposal.person_id not in self._session.person_ids:
            raise ProposalNotFoundError
        opening = await self._opening_of(proposal)
        number = await self._ports.writer.save(opening)
        logger.info("Protocolo confirmado: serviço %s", opening.service_code)
        return ConfirmedProtocolDto.of(number, opening)

    async def _opening_of(self, proposal: SignedProposal) -> ProtocolOpening:
        parties = await self._parties_of(proposal)
        existing = await self._ports.protocols.list_protocols()
        entry = ServiceActions.find(proposal.service_code)
        if entry is None:
            raise ProposalNotFoundError
        request = OpeningRequest(parties.requester_name, entry.request_text, self._clock.today())
        return ProtocolOpening.open(parties.service, parties.enrollment, existing, request)

    async def _parties_of(self, proposal: SignedProposal) -> OpeningParties:
        services, enrollments, name = await asyncio.gather(
            self._ports.protocols.list_services(),
            self._ports.academic.list_enrollments(),
            self._ports.requesters.full_name_of(proposal.person_id),
        )
        service = next((item for item in services if item.code == proposal.service_code), None)
        enrollment = next(
            (item for item in enrollments if item.reference == proposal.enrollment), None
        )
        if service is None or enrollment is None or not name:
            raise ProposalNotFoundError
        return OpeningParties(service, enrollment, name)

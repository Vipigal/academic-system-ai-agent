import asyncio

from api.application.protocol.confirmation_ports import ConfirmationPorts, OpeningParties
from api.domain.protocol.action import ServiceAction
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.errors import ProposalNotFoundError
from api.domain.protocol.proposal import SignedProposal


class ProposalParties:
    def __init__(self, ports: ConfirmationPorts) -> None:
        self._ports = ports

    async def of(self, proposal: SignedProposal) -> OpeningParties:
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
        return OpeningParties(service, enrollment, self._action_of(proposal), name)

    @staticmethod
    def _action_of(proposal: SignedProposal) -> ServiceAction:
        action = ServiceActions.proposable(proposal.service_code)
        if action is None:
            raise ProposalNotFoundError
        return action

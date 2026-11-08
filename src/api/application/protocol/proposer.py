import asyncio

from api.application.protocol.dto.proposal import Proposal
from api.application.protocol.proposal_results import ProposalResults
from api.application.protocol.scope import EnrollmentChoice
from api.application.shared.tool_result import ToolResult
from api.domain.identity.session import StudentSession
from api.domain.ports.academic import StudentAcademicRepository
from api.domain.ports.protocol import ProposalSigner, ProtocolRepository
from api.domain.protocol.action import ProtocolAction, ServiceAction
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.catalog import Service
from api.domain.protocol.proposal import SignedProposal


class ProtocolProposer:
    def __init__(
        self,
        protocols: ProtocolRepository,
        academic: StudentAcademicRepository,
        signer: ProposalSigner,
        session: StudentSession,
    ) -> None:
        self._protocols = protocols
        self._academic = academic
        self._signer = signer
        self._session = session

    async def propose(
        self, action: ProtocolAction, enrollment: str, subject: str | None
    ) -> ToolResult[Proposal]:
        entry = ServiceActions.of_action(action)
        services = await self._protocols.list_services()
        service = next((item for item in services if item.code == entry.code), None)
        if service is None:
            return ToolResult.not_found(())
        cited = (subject or "").strip() or None
        refused = ProposalResults.service_refusal(service, entry, cited)
        if refused is not None:
            return refused
        return await self._for_enrollment(service, entry, enrollment, cited)

    async def _for_enrollment(
        self, service: Service, entry: ServiceAction, enrollment: str, subject: str | None
    ) -> ToolResult[Proposal]:
        enrollments, protocols = await asyncio.gather(
            self._academic.list_enrollments(), self._protocols.list_protocols()
        )
        choice = EnrollmentChoice.of(enrollments, enrollment)
        if choice.selected is None:
            return ToolResult.not_found(choice.candidates)
        refused = ProposalResults.enrollment_refusal(service, entry, choice.selected, protocols)
        if refused is not None:
            return refused
        token = self._signer.sign(SignedProposal.of(self._session, service, choice.selected))
        return ProposalResults.proposed(service, entry, choice.selected, subject, token)

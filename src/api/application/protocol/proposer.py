import asyncio

from api.application.protocol.dto.proposal import (
    Proposal,
    ProtocolProposalDto,
    ProtocolRefusalDto,
)
from api.application.protocol.scope import EnrollmentChoice, ProtocolCandidates
from api.application.shared.name_search import NameSearch
from api.application.shared.tool_result import ToolResult
from api.domain.academic.enrollment import Enrollment
from api.domain.identity.session import StudentSession
from api.domain.ports.academic import StudentAcademicRepository
from api.domain.ports.protocol import ProposalSigner, ProtocolRepository
from api.domain.protocol.catalog import Service
from api.domain.protocol.proposal import ProposalRules, RefusalReason, SignedProposal


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
        self, service: str, enrollment: str | None, message: str
    ) -> ToolResult[Proposal]:
        services = await self._protocols.list_services()
        search = NameSearch.search(service, ProtocolCandidates.of_services(services))
        if search.missed:
            return ToolResult.not_found(search.candidates)
        if search.is_ambiguous:
            return ToolResult.ambiguous(search.matched)
        chosen = next(item for item in services if item.code in search.codes)
        reason = ProposalRules.refusal(chosen, message)
        if reason is not None:
            return ToolResult.refused(ProtocolRefusalDto.of(reason, chosen))
        return await self._for_enrollment(chosen, enrollment, message)

    async def _for_enrollment(
        self, service: Service, enrollment: str | None, message: str
    ) -> ToolResult[Proposal]:
        enrollments, protocols = await asyncio.gather(
            self._academic.list_enrollments(), self._protocols.list_protocols()
        )
        choice = EnrollmentChoice.of(enrollments, enrollment)
        if choice.selected is None:
            if choice.is_ambiguous:
                return ToolResult.ambiguous(choice.candidates)
            return ToolResult.not_found(choice.candidates)
        duplicate = ProposalRules.duplicate_of(protocols, service, choice.selected)
        if duplicate is not None:
            reason = RefusalReason.DUPLICATE_IN_PROGRESS
            return ToolResult.refused(ProtocolRefusalDto.of(reason, service, duplicate.number))
        return self._signed(service, choice.selected, message)

    def _signed(
        self, service: Service, enrollment: Enrollment, message: str
    ) -> ToolResult[Proposal]:
        signed = SignedProposal.of(self._session, service, enrollment, message)
        proposal = ProtocolProposalDto.of(service, enrollment, message)
        token = self._signer.sign(signed)
        return ToolResult[Proposal].ok(proposal).with_client_only({"token": token})

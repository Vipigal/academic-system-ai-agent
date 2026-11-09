from collections.abc import Sequence

from api.application.protocol.dto.proposal import (
    Proposal,
    ProposalConfirmation,
    ProtocolProposalDto,
    ProtocolRefusalDto,
    RefusalExplanation,
)
from api.application.shared.tool_result import ClientOnly, ToolResult
from api.domain.academic.enrollment import Enrollment
from api.domain.protocol.action import ServiceAction
from api.domain.protocol.catalog import Service
from api.domain.protocol.proposal import ProposalRules, RefusalReason
from api.domain.protocol.request import Protocol


class ProposalResults:
    @staticmethod
    def service_refusal(
        service: Service, entry: ServiceAction, subject: str | None
    ) -> ToolResult[Proposal] | None:
        if ProposalRules.action_refusal(entry, subject) is not None:
            refused = ProtocolRefusalDto.of(RefusalReason.SUBJECT_NOT_SUPPORTED, service)
            return ToolResult.refused(refused, explanation=RefusalExplanation.of_subject(entry))
        reason = ProposalRules.refusal(service)
        if reason is None:
            return None
        return ToolResult.refused(ProtocolRefusalDto.of(reason, service))

    @staticmethod
    def enrollment_refusal(
        service: Service,
        entry: ServiceAction,
        enrollment: Enrollment,
        protocols: Sequence[Protocol],
    ) -> ToolResult[Proposal] | None:
        if ProposalRules.enrollment_refusal(entry, enrollment) is not None:
            refused = ProtocolRefusalDto.of(RefusalReason.ENROLLMENT_STATUS, service)
            explanation = RefusalExplanation.of_status(entry, enrollment)
            return ToolResult.refused(refused, explanation=explanation)
        duplicate = ProposalRules.duplicate_of(protocols, service, enrollment)
        if duplicate is None:
            return None
        reason = RefusalReason.DUPLICATE_IN_PROGRESS
        return ToolResult.refused(ProtocolRefusalDto.of(reason, service, duplicate.number))

    @staticmethod
    def proposed(
        service: Service,
        entry: ServiceAction,
        enrollment: Enrollment,
        subject: str | None,
        token: str,
    ) -> ToolResult[Proposal]:
        proposal = ProtocolProposalDto.of(service, entry, enrollment, subject)
        confirmation = ProposalConfirmation.block(entry, enrollment)
        client_only: ClientOnly = {"token": token, "confirmation": confirmation}
        return ToolResult[Proposal].ok(proposal).with_client_only(client_only)

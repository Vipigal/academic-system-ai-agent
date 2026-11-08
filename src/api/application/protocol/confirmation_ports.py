from dataclasses import dataclass, field

from api.domain.academic.enrollment import Enrollment
from api.domain.ports.academic import StudentAcademicRepository
from api.domain.ports.conversation import ConversationRepository
from api.domain.ports.identity import RequesterDirectory
from api.domain.ports.protocol import ProposalSigner, ProtocolRepository, ProtocolWriter
from api.domain.protocol.action import ServiceAction
from api.domain.protocol.catalog import Service


@dataclass(frozen=True, slots=True)
class ConfirmationPorts:
    signer: ProposalSigner
    protocols: ProtocolRepository
    academic: StudentAcademicRepository
    requesters: RequesterDirectory
    writer: ProtocolWriter
    conversations: ConversationRepository


@dataclass(frozen=True, slots=True)
class OpeningParties:
    service: Service
    enrollment: Enrollment
    action: ServiceAction
    requester_name: str = field(repr=False)

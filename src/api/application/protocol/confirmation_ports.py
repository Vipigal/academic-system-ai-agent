from dataclasses import dataclass, field

from api.domain.academic.enrollment import Enrollment
from api.domain.ports.academic import StudentAcademicRepository
from api.domain.ports.identity import RequesterDirectory
from api.domain.ports.protocol import ProposalSigner, ProtocolRepository, ProtocolWriter
from api.domain.protocol.catalog import Service


@dataclass(frozen=True, slots=True)
class ConfirmationPorts:
    signer: ProposalSigner
    protocols: ProtocolRepository
    academic: StudentAcademicRepository
    requesters: RequesterDirectory
    writer: ProtocolWriter


@dataclass(frozen=True, slots=True)
class OpeningParties:
    service: Service
    enrollment: Enrollment
    requester_name: str = field(repr=False)

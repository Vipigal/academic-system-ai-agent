from api.application.protocol.confirmation_ports import ConfirmationPorts
from api.bootstrap.history_providers import HistoryProviders
from api.domain.ports.protocol import ProposalSigner
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.requester_directory import SqlRequesterDirectory
from api.persistence.sag.student_repository import SagStudentAcademicRepository
from api.persistence.secretary.protocol_writer import SqlProtocolWriter
from api.persistence.secretary.repository import SqlProtocolRepository


class ProtocolConfirmationPorts:
    @staticmethod
    def of(adapter: RepositoryAdapter, signer: ProposalSigner) -> ConfirmationPorts:
        return ConfirmationPorts(
            signer=signer,
            protocols=SqlProtocolRepository(adapter),
            academic=SagStudentAcademicRepository(adapter),
            requesters=SqlRequesterDirectory(adapter),
            writer=SqlProtocolWriter(adapter),
            conversations=HistoryProviders(adapter).conversations(),
        )

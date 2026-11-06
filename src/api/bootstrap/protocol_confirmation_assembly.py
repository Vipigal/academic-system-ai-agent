from api.application.protocol.confirmation import ProtocolConfirmation
from api.application.protocol.confirmation_ports import ConfirmationPorts
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.protocol import ProposalSigner
from api.infrastructure.tracing import CurrentTrace
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository
from api.persistence.sag.student_repository import SagStudentAcademicRepository
from api.persistence.secretary.protocol_writer import SqlProtocolWriter
from api.persistence.secretary.repository import SqlProtocolRepository


class ProtocolConfirmationAssembly:
    def __init__(self, database: Database, clock: Clock, signer: ProposalSigner) -> None:
        self._database = database
        self._clock = clock
        self._signer = signer

    def for_session(self, session: StudentSession) -> ProtocolConfirmation:
        factory = self._database.db_session_factory
        adapter = RepositoryAdapter(factory, session)
        ports = ConfirmationPorts(
            signer=self._signer,
            protocols=SqlProtocolRepository(adapter),
            academic=SagStudentAcademicRepository(adapter),
            requesters=StudentSessionRepository(factory),
            writer=SqlProtocolWriter(adapter),
        )
        return ProtocolConfirmation(session, ports, self._clock, CurrentTrace())

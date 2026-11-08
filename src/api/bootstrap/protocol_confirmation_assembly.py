from api.application.protocol.confirmation import ProtocolConfirmation
from api.bootstrap.protocol_confirmation_ports import ProtocolConfirmationPorts
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.protocol import ProposalSigner
from api.infrastructure.tracing import CurrentTrace
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter


class ProtocolConfirmationAssembly:
    def __init__(
        self,
        database: Database,
        clock: Clock,
        signer: ProposalSigner,
        trace: CurrentTrace | None = None,
    ) -> None:
        self._database = database
        self._clock = clock
        self._signer = signer
        self._trace = trace or CurrentTrace()

    def for_session(self, session: StudentSession) -> ProtocolConfirmation:
        adapter = RepositoryAdapter(self._database.db_session_factory, session)
        ports = ProtocolConfirmationPorts.of(adapter, self._signer)
        return ProtocolConfirmation(session, ports, self._clock, self._trace)

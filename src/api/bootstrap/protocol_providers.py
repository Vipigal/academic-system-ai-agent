from api.application.protocol.proposer import ProtocolProposer
from api.application.protocol.queries import ProtocolQueries
from api.application.protocol.service import ProtocolService
from api.application.protocol.source import ProtocolSource
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.domain.ports.protocol import ProposalSigner
from api.infrastructure.proposal_signer import ProposalJwtSigner
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.sag.student_repository import SagStudentAcademicRepository
from api.persistence.secretary.repository import SqlProtocolRepository


class ProtocolProviders:
    def __init__(self, adapter: RepositoryAdapter, clock: Clock, signer: ProposalSigner) -> None:
        self._adapter = adapter
        self._clock = clock
        self._signer = signer

    @staticmethod
    def signer_of(settings: Settings) -> ProposalSigner:
        secret = settings.proposal_secret
        return ProposalJwtSigner(
            secret.get_secret_value() if secret else "", settings.proposal_ttl_minutes
        )

    def service(self) -> ProtocolService:
        protocols = SqlProtocolRepository(self._adapter)
        finance = SqlFinanceRepository(self._adapter)
        source = ProtocolSource(protocols, finance, self._clock)
        proposer = ProtocolProposer(
            protocols,
            SagStudentAcademicRepository(self._adapter),
            self._signer,
            self._adapter.student_session,
        )
        return ProtocolService(ProtocolQueries(source), proposer)

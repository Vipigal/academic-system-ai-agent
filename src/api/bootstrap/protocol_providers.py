from api.application.protocol.proposer import ProtocolProposer
from api.application.protocol.queries import ProtocolQueries
from api.application.protocol.service import ProtocolService
from api.application.protocol.source import ProtocolSource
from api.domain.ports.clock import Clock
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.sag.student_repository import SagStudentAcademicRepository
from api.persistence.secretary.repository import SqlProtocolRepository


class ProtocolProviders:
    def __init__(self, adapter: RepositoryAdapter, clock: Clock) -> None:
        self._adapter = adapter
        self._clock = clock

    def service(self) -> ProtocolService:
        protocols = SqlProtocolRepository(self._adapter)
        finance = SqlFinanceRepository(self._adapter)
        source = ProtocolSource(protocols, finance, self._clock)
        proposer = ProtocolProposer(protocols, SagStudentAcademicRepository(self._adapter))
        return ProtocolService(ProtocolQueries(source), proposer)

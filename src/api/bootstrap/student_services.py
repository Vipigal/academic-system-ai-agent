from api.application.academic.service import AcademicService
from api.application.finance.service import FinancialService
from api.application.lms.service import LmsService
from api.application.overview.service import OverviewService
from api.application.protocol.service import ProtocolService
from api.bootstrap.protocol_providers import ProtocolProviders
from api.domain.ports.clock import Clock
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.lms.repository import SqlLmsRepository
from api.persistence.sag.catalog_repository import SagAcademicCatalogRepository
from api.persistence.sag.student_repository import SagStudentAcademicRepository


class StudentServices:
    def __init__(
        self, adapter: RepositoryAdapter, clock: Clock, protocols: ProtocolProviders
    ) -> None:
        self._adapter = adapter
        self._clock = clock
        self._protocols = protocols

    def academic(self) -> AcademicService:
        return AcademicService(
            SagAcademicCatalogRepository(self._adapter),
            SagStudentAcademicRepository(self._adapter),
            self._clock,
        )

    def financial(self) -> FinancialService:
        return FinancialService(SqlFinanceRepository(self._adapter), self._clock)

    def protocol(self) -> ProtocolService:
        return self._protocols.service()

    def lms(self) -> LmsService:
        return LmsService(
            SqlLmsRepository(self._adapter),
            SagAcademicCatalogRepository(self._adapter),
            SagStudentAcademicRepository(self._adapter),
            self._clock,
        )

    def overview(self) -> OverviewService:
        return OverviewService(
            self.academic(), self.financial(), self.protocol(), self.lms(), self._clock
        )

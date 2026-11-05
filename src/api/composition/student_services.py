from api.application.academic_service import AcademicService
from api.application.financial_service import FinancialService
from api.application.lms_service import LmsService
from api.application.overview_service import OverviewService
from api.application.protocol_proposer import ProtocolProposer
from api.application.protocol_queries import ProtocolQueries
from api.application.protocol_service import ProtocolService
from api.application.protocol_source import ProtocolSource
from api.composition.student_repositories import StudentRepositories
from api.domain.ports.clock import Clock


class StudentServices:
    def __init__(self, repositories: StudentRepositories, clock: Clock) -> None:
        self._repositories = repositories
        self._clock = clock

    def academic(self) -> AcademicService:
        repositories = self._repositories
        return AcademicService(
            repositories.academic_catalog, repositories.academic_student, self._clock
        )

    def financial(self) -> FinancialService:
        return FinancialService(self._repositories.finance, self._clock)

    def protocol(self) -> ProtocolService:
        repositories = self._repositories
        source = ProtocolSource(repositories.protocols, repositories.finance, self._clock)
        proposer = ProtocolProposer(repositories.protocols, repositories.academic_student)
        return ProtocolService(ProtocolQueries(source), proposer)

    def lms(self) -> LmsService:
        repositories = self._repositories
        return LmsService(
            repositories.lms,
            repositories.academic_catalog,
            repositories.academic_student,
            self._clock,
        )

    def overview(self) -> OverviewService:
        return OverviewService(
            self.academic(), self.financial(), self.protocol(), self.lms(), self._clock
        )

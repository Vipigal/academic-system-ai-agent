from api.application.lms_service import LmsService
from api.application.protocol_proposer import ProtocolProposer
from api.application.protocol_queries import ProtocolQueries
from api.application.protocol_service import ProtocolService
from api.application.protocol_source import ProtocolSource
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.lms.lms_repository import SqlLmsRepository
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.sag.academic_catalog_repository import SagAcademicCatalogRepository
from api.persistence.sag.academic_student_repository import SagStudentAcademicRepository
from api.persistence.secretary.protocol_repository import SqlProtocolRepository
from tests.integration.tool_support import FixedClock


def protocol_service(adapter: RepositoryAdapter, clock: FixedClock) -> ProtocolService:
    protocols = SqlProtocolRepository(adapter)
    source = ProtocolSource(protocols, SqlFinanceRepository(adapter), clock)
    proposer = ProtocolProposer(protocols, SagStudentAcademicRepository(adapter))
    return ProtocolService(ProtocolQueries(source), proposer)


def lms_service(adapter: RepositoryAdapter, clock: FixedClock) -> LmsService:
    return LmsService(
        SqlLmsRepository(adapter),
        SagAcademicCatalogRepository(adapter),
        SagStudentAcademicRepository(adapter),
        clock,
    )

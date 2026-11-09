from dishka import AnyOf, Provider, Scope, provide, provide_all

from api.application.academic.service import AcademicService
from api.application.finance.service import FinancialService
from api.application.lms.service import LmsService
from api.domain.ports.academic import AcademicCatalogRepository, StudentAcademicRepository
from api.domain.ports.finance import FinanceRepository, ServiceFeeRepository
from api.domain.ports.lms import LmsRepository
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.lms.repository import SqlLmsRepository
from api.persistence.sag.catalog_repository import SagAcademicCatalogRepository
from api.persistence.sag.student_repository import SagStudentAcademicRepository


class StudentProvider(Provider):
    scope = Scope.REQUEST

    adapter = provide(RepositoryAdapter)
    finance = provide(SqlFinanceRepository, provides=AnyOf[FinanceRepository, ServiceFeeRepository])
    catalog = provide(SagAcademicCatalogRepository, provides=AcademicCatalogRepository)
    academic = provide(SagStudentAcademicRepository, provides=StudentAcademicRepository)
    lms = provide(SqlLmsRepository, provides=LmsRepository)
    services = provide_all(AcademicService, FinancialService, LmsService)

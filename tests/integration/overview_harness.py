from api.application.academic_service import AcademicService
from api.application.financial_service import FinancialService
from api.application.overview_service import OverviewService
from api.persistence.database import Database
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.sag.academic_catalog_repository import SagAcademicCatalogRepository
from api.persistence.sag.academic_student_repository import SagStudentAcademicRepository
from api.presentation.tools.overview_tools import OverviewTools
from tests.integration import overview_parts
from tests.integration.protocol_harness import adapter_for
from tests.integration.tool_support import FixedClock


async def tools_for(database: Database, person_id: str) -> OverviewTools:
    adapter = await adapter_for(database, person_id)
    clock = FixedClock()
    academic = AcademicService(
        SagAcademicCatalogRepository(adapter), SagStudentAcademicRepository(adapter), clock
    )
    financial = FinancialService(SqlFinanceRepository(adapter), clock)
    return OverviewTools(
        OverviewService(
            academic,
            financial,
            overview_parts.protocol_service(adapter, clock),
            overview_parts.lms_service(adapter, clock),
            clock,
        )
    )

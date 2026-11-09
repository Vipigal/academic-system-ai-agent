from unittest.mock import AsyncMock, MagicMock

from api.application.academic.service import AcademicService
from api.application.agent.student_tools import StudentTools
from api.application.agent.tools import academic, finance, lms, overview, protocol
from api.application.finance.service import FinancialService
from api.application.lms.service import LmsService
from api.application.overview.service import OverviewService
from api.application.protocol.service import ProtocolService
from api.application.shared.tool_result import ToolResult

STUB_DATA = "dados do aluno"


def stub_service(service_class: type) -> MagicMock:
    service = MagicMock(spec=service_class)
    for name in dir(service_class):
        method = getattr(service, name)
        if not name.startswith("_") and isinstance(method, AsyncMock):
            method.return_value = ToolResult.ok(STUB_DATA)
    return service


def stub_student() -> StudentTools:
    return StudentTools(
        academic=academic.AcademicTools(stub_service(AcademicService)),
        finance=finance.FinanceTools(stub_service(FinancialService)),
        protocol=protocol.ProtocolTools(stub_service(ProtocolService)),
        lms=lms.LmsTools(stub_service(LmsService)),
        overview=overview.OverviewTools(stub_service(OverviewService)),
    )

from dishka import Provider, Scope, provide, provide_all

from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.academic import AcademicTools
from api.application.agent.tools.finance import FinanceTools
from api.application.agent.tools.lms import LmsTools
from api.application.agent.tools.overview import OverviewTools
from api.application.agent.tools.protocol import ProtocolTools
from api.application.overview.service import OverviewService


class ToolProvider(Provider):
    scope = Scope.REQUEST

    overview = provide(OverviewService)
    tools = provide_all(AcademicTools, FinanceTools, ProtocolTools, LmsTools, OverviewTools)
    student_tools = provide(StudentTools)

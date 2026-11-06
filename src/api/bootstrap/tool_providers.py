from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.academic import AcademicTools
from api.application.agent.tools.finance import FinanceTools
from api.application.agent.tools.lms import LmsTools
from api.application.agent.tools.overview import OverviewTools
from api.application.agent.tools.protocol import ProtocolTools
from api.bootstrap.student_services import StudentServices


class ToolProviders:
    @staticmethod
    def tools_for(services: StudentServices) -> StudentTools:
        return StudentTools(
            academic=AcademicTools(services.academic()),
            finance=FinanceTools(services.financial()),
            protocol=ProtocolTools(services.protocol()),
            lms=LmsTools(services.lms()),
            overview=OverviewTools(services.overview()),
        )

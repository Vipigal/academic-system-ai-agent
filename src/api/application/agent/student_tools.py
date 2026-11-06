from dataclasses import dataclass

from api.application.agent.tools.academic import AcademicTools
from api.application.agent.tools.finance import FinanceTools
from api.application.agent.tools.lms import LmsTools
from api.application.agent.tools.overview import OverviewTools
from api.application.agent.tools.protocol import ProtocolTools
from api.application.agent.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class StudentTools:
    academic: AcademicTools
    finance: FinanceTools
    protocol: ProtocolTools
    lms: LmsTools
    overview: OverviewTools

    def registry(self) -> ToolRegistry:
        return ToolRegistry(self.academic, self.finance, self.protocol, self.lms, self.overview)

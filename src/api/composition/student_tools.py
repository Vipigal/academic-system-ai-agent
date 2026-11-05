from dataclasses import dataclass
from typing import Self

from api.composition.student_services import StudentServices
from api.presentation.tools.academic_tools import AcademicTools
from api.presentation.tools.finance_tools import FinanceTools
from api.presentation.tools.lms_tools import LmsTools
from api.presentation.tools.overview_tools import OverviewTools
from api.presentation.tools.protocol_tools import ProtocolTools
from api.presentation.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class StudentTools:
    academic: AcademicTools
    finance: FinanceTools
    protocol: ProtocolTools
    lms: LmsTools
    overview: OverviewTools

    @classmethod
    def of(cls, services: StudentServices) -> Self:
        return cls(
            academic=AcademicTools(services.academic()),
            finance=FinanceTools(services.financial()),
            protocol=ProtocolTools(services.protocol()),
            lms=LmsTools(services.lms()),
            overview=OverviewTools(services.overview()),
        )

    def registry(self) -> ToolRegistry:
        return ToolRegistry(self.academic, self.finance, self.protocol, self.lms, self.overview)

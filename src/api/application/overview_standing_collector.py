import asyncio

from api.application.academic_service import AcademicService
from api.application.dto.overview_pending_dto import PendingArea
from api.application.financial_service import FinancialService
from api.application.overview_findings import Findings
from api.application.overview_pages import Gathered
from api.application.overview_standing import StandingRules
from api.domain.ports.clock import Clock


class StandingCollector:
    def __init__(
        self, academic: AcademicService, financial: FinancialService, clock: Clock
    ) -> None:
        self._academic = academic
        self._financial = financial
        self._clock = clock

    async def collect(self) -> Findings:
        enrollment_result, summary_result, invoices = await asyncio.gather(
            self._academic.list_enrollments(),
            self._financial.get_financial_summary(),
            Gathered.of_pages(lambda page: self._financial.list_invoices(page=page)),
        )
        enrollments = Gathered.of_result(enrollment_result)
        summary = Gathered.of_result(summary_result)
        return Findings(
            {
                PendingArea.ENROLLMENT: StandingRules.enrollments(enrollments.items),
                PendingArea.DEBT: StandingRules.debts(summary.items),
                PendingArea.UPCOMING_INVOICES: StandingRules.upcoming_invoices(
                    invoices.items, self._clock.today()
                ),
            },
            (),
        )

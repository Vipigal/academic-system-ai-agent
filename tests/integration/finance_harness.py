from typing import Any

from api.application.dto.invoice_dto import InvoiceDto
from api.application.dto.tool_result import ToolResult
from api.application.financial_service import FinancialService
from api.application.page import PageRequest
from api.persistence.database import Database
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.student_session_repository import StudentSessionRepository
from api.presentation.tools.finance_tools import FinanceTools
from tests.integration.tool_support import FixedClock

SNAPSHOT_TOTAL = (
    "SELECT totaldebtcents FROM finance.receivable_snapshot "
    "WHERE contractid = :contract AND snapshotdate = '2026-10-31'"
)

type InvoicePage = ToolResult[list[InvoiceDto]]


class FinanceHarness:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def tools_for(self, person_id: str) -> FinanceTools:
        factory = self._database.db_session_factory
        session = await StudentSessionRepository(factory).load(person_id)
        repository = SqlFinanceRepository(RepositoryAdapter(factory, session))
        return FinanceTools(FinancialService(repository, FixedClock()))

    async def summary_of(self, person_id: str, contract: str) -> dict[str, Any]:
        tools = await self.tools_for(person_id)
        result = await tools.get_financial_summary()
        found = next(item for item in result.data or [] if item.contract_id == contract)
        return found.model_dump(mode="json")

    async def agreement_of(self, person_id: str, agreement: str) -> dict[str, Any]:
        tools = await self.tools_for(person_id)
        result = await tools.list_agreements()
        return next(
            item.model_dump(mode="json") for item in result.data or [] if item.id == agreement
        )

    async def invoice_pages(self, person_id: str, limit: int) -> list[InvoicePage]:
        tools = await self.tools_for(person_id)
        pages: list[InvoicePage] = []
        offset: int | None = 0
        while offset is not None:
            pages.append(await tools.list_invoices(page=PageRequest(offset=offset, limit=limit)))
            offset = pages[-1].page.next_offset if pages[-1].page else None
        return pages

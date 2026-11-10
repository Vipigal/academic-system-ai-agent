from typing import Any

from api.application.agent.tool_arguments import BoundedPage
from api.application.agent.tools.finance import FinanceTools
from api.application.finance.dto.invoice import InvoiceDto
from api.application.shared.tool_result import ToolResult
from api.persistence.core.database import Database
from tests.integration.support.tools import student_tools

SNAPSHOT_TOTAL = (
    "SELECT totaldebtcents FROM finance.receivable_snapshot "
    "WHERE contractid = :contract AND snapshotdate = '2026-10-31'"
)

type InvoicePage = ToolResult[list[InvoiceDto]]


class FinanceHarness:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def tools_for(self, person_id: str) -> FinanceTools:
        return (await student_tools(self._database, person_id)).finance

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
            pages.append(await tools.list_invoices(page=BoundedPage(offset=offset, limit=limit)))
            offset = pages[-1].page.next_offset if pages[-1].page else None
        return pages

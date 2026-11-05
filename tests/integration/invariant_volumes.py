from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from api.application.page import PageRequest
from api.domain.session import StudentSession
from api.persistence.lms.vocabulary import MATERIAL_KIND_BY_SOURCE, VIEW_EVENTS
from api.presentation.tools.registry import ToolRegistry
from tests.integration import invariant_queries, invariant_support
from tests.integration.invariant_json import Output
from tests.integration.sql_oracle import SqlOracle

PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class Count:
    returned: int
    expected: int


class Volumes:
    def __init__(self, oracle: SqlOracle, registry: ToolRegistry, session: StudentSession) -> None:
        self._oracle = oracle
        self._handlers: Mapping[str, Callable[..., Any]] = {
            tool.definition.name: tool.handler for tool in registry.tools
        }
        self._session = session
        self._accounts = invariant_support.joined(session.lms_user_ids)

    async def attempts(self) -> Count:
        items = await self._walk("list_online_exams")
        returned = sum(len(item["attempts"]) for item in items)
        expected = await self._oracle.count(
            invariant_queries.OWN_ATTEMPT_COUNT, accounts=self._accounts
        )
        return Count(returned, expected)

    async def views(self) -> list[Count]:
        expected = await self._counted(
            invariant_queries.OWN_VIEWS_BY_SUBJECT,
            accounts=self._accounts,
            events=",".join(VIEW_EVENTS),
            kinds=",".join(MATERIAL_KIND_BY_SOURCE),
        )
        subjects = await self._oracle.values(
            invariant_queries.OWN_SUBJECTS,
            enrollments=invariant_support.joined(invariant_support.enrollment_refs(self._session)),
        )
        return [
            Count(
                sum(
                    item["view_count"]
                    for item in await self._walk("list_material_views", subject=subject)
                ),
                expected.get(subject, 0),
            )
            for subject in sorted(subjects | expected.keys())
        ]

    async def protocols(self) -> list[Count]:
        numbers = invariant_support.joined(self._session.protocol_ids)
        expected = {
            "messages": await self._counted(
                invariant_queries.PUBLIC_MESSAGES_BY_PROTOCOL, protocols=numbers
            ),
            "history": await self._counted(
                invariant_queries.HISTORY_BY_PROTOCOL, protocols=numbers
            ),
        }
        details = {number: await self._detail(number) for number in self._session.protocol_ids}
        return [
            Count(len(detail[part]), expected[part].get(number, 0))
            for number, detail in sorted(details.items())
            for part in expected
        ]

    async def _detail(self, number: str) -> Output:
        result = await self._handlers["get_protocol"](number=number)
        return dict(result.model_dump(mode="json")["data"])

    async def _walk(self, tool: str, **arguments: object) -> list[Output]:
        items: list[Output] = []
        offset: int | None = 0
        while offset is not None:
            request = PageRequest(offset=offset, limit=PAGE_SIZE)
            result = await self._handlers[tool](**arguments, page=request)
            items.extend(result.model_dump(mode="json", by_alias=True).get("data") or [])
            offset = result.page.next_offset if result.page else None
        return items

    async def _counted(self, sql: str, **parameters: str) -> dict[str, int]:
        pairs = await self._oracle.values(sql, **parameters)
        return {key: int(count) for key, count in (pair.rsplit(":", 1) for pair in pairs)}

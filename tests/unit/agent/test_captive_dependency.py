import gc
from collections.abc import Iterable
from types import FunctionType, ModuleType

from api.application.agent.student_agent import StudentAgent
from api.application.agent.tools import academic, finance, lms, overview, protocol
from api.application.finance.service import FinancialService
from tests.unit.agent import agent_support as support
from tests.unit.agent.student_stubs import stub_service, stub_student

MAX_WALK = 200_000
TOOL_GROUPS = (
    academic.AcademicTools,
    finance.FinanceTools,
    protocol.ProtocolTools,
    lms.LmsTools,
    overview.OverviewTools,
)


def reachable_from(roots: Iterable[object]) -> list[object]:
    seen: set[int] = set()
    found: list[object] = []
    pending = list(roots)
    while pending and len(seen) < MAX_WALK:
        item = pending.pop()
        if id(item) in seen or isinstance(item, type | ModuleType | FunctionType):
            continue
        seen.add(id(item))
        found.append(item)
        pending.extend(gc.get_referents(item))
    return found


def tool_groups_in(reached: Iterable[object]) -> list[object]:
    return [item for item in reached if isinstance(item, TOOL_GROUPS)]


async def test_two_students_in_a_row_get_tools_bound_to_their_own_services() -> None:
    first = stub_service(FinancialService)
    second = stub_service(FinancialService)
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer()]
    )
    runtime = support.runtime_with(model)

    tools = support.registered_of(finance.FinanceTools(first))
    await StudentAgent(runtime, tools, "um").run("Quanto devo?")
    first.get_financial_summary.assert_awaited_once()
    second.get_financial_summary.assert_not_awaited()

    tools = support.registered_of(finance.FinanceTools(second))
    await StudentAgent(runtime, tools, "dois").run("Quanto devo?")
    first.get_financial_summary.assert_awaited_once()
    second.get_financial_summary.assert_awaited_once()


async def test_nothing_that_lives_the_whole_process_reaches_a_student() -> None:
    student = stub_student()
    model = support.RecordingModel(
        responses=[support.call("get_financial_summary"), support.answer()]
    )
    runtime = support.runtime_with(model)

    await StudentAgent(runtime, student.registry().tools, "trace").run("Quanto devo?")
    model.seen.clear()

    assert not tool_groups_in(reachable_from((runtime,)))
    assert tool_groups_in(reachable_from((student,)))

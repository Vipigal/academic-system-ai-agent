from collections.abc import Mapping

from evals.execution import Execution, ToolStep
from evals.golden.items import GoldenItem
from evals.item_context import ForeignIdentifiers, ItemContext
from tests.unit.evals.items_support import question


def context_of(
    item: GoldenItem | None = None,
    forbidden: tuple[str, ...] = (),
    foreign: frozenset[str] = frozenset(),
) -> ItemContext:
    graded = item or question()
    return ItemContext(
        item=graded,
        question=graded.question,
        forbidden_values=forbidden,
        foreign=ForeignIdentifiers.of(foreign),
    )


def step(name: str, status: str = "ok", output: Mapping[str, object] | None = None) -> ToolStep:
    return ToolStep(name, {}, status, 3, output or {"status": status})


def execution_of(answer: str, *steps: ToolStep) -> Execution:
    return Execution("FI-01", 1, "Quanto estou devendo hoje?", answer, steps)

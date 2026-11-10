from collections.abc import Mapping

from evals.dataset.items import DatasetItem
from evals.execution import Execution, ToolStep
from evals.item_context import ForeignIdentifiers, ItemContext
from tests.unit.evals.items_support import question


def context_of(
    item: DatasetItem | None = None,
    forbidden: tuple[str, ...] = (),
    foreign: frozenset[str] = frozenset(),
) -> ItemContext:
    graded = (item or question()).model_copy(update={"forbidden_values": forbidden})
    return ItemContext(item=graded, foreign=ForeignIdentifiers.of(foreign))


def step(name: str, status: str = "ok", output: Mapping[str, object] | None = None) -> ToolStep:
    return ToolStep(name, {}, status, 3, output or {"status": status})


def execution_of(answer: str, *steps: ToolStep) -> Execution:
    return Execution("FI-01", 1, "Quanto estou devendo hoje?", answer, steps)

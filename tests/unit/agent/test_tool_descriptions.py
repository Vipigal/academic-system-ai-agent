import json
from pathlib import Path

import pytest

from api.application.agent.tools.academic import AcademicTools
from api.application.agent.tools.finance import FinanceTools
from api.application.agent.tools.lms import LmsTools
from api.application.agent.tools.overview import OverviewTools
from api.application.agent.tools.protocol import ProtocolTools
from api.application.agent.tools.registry import ToolRegistry

SNAPSHOTS = Path(__file__).parent / "tool_descriptions"


@pytest.mark.parametrize(
    "group",
    [AcademicTools, FinanceTools, ProtocolTools, LmsTools, OverviewTools],
)
def test_descriptions_match_the_group_snapshot(group: type) -> None:
    snapshot = json.loads((SNAPSHOTS / f"{group.__name__}.json").read_text(encoding="utf-8"))

    described = {tool.name: tool.description for tool in ToolRegistry.describe(group)}

    assert described == snapshot

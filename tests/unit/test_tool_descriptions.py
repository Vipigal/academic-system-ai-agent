import json
from pathlib import Path

import pytest

from api.presentation.tools.academic_tools import AcademicTools
from api.presentation.tools.finance_tools import FinanceTools
from api.presentation.tools.lms_tools import LmsTools
from api.presentation.tools.overview_tools import OverviewTools
from api.presentation.tools.protocol_tools import ProtocolTools
from api.presentation.tools.registry import ToolRegistry

SNAPSHOTS = Path(__file__).parent / "tool_descriptions"


@pytest.mark.parametrize(
    "group",
    [AcademicTools, FinanceTools, ProtocolTools, LmsTools, OverviewTools],
)
def test_descriptions_match_the_group_snapshot(group: type) -> None:
    snapshot = json.loads((SNAPSHOTS / f"{group.__name__}.json").read_text(encoding="utf-8"))

    described = {tool.name: tool.description for tool in ToolRegistry.describe(group)}

    assert described == snapshot

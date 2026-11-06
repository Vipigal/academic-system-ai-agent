from typing import get_type_hints

from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.registry import ToolRegistry
from api.application.agent.tools.skill_tools import SkillTools


class ToolNames:
    @staticmethod
    def registered() -> frozenset[str]:
        groups = (*get_type_hints(StudentTools).values(), SkillTools)
        return frozenset(tool.name for group in groups for tool in ToolRegistry.describe(group))

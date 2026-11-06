import hashlib
from typing import get_type_hints

from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.registry import ToolDefinition, ToolRegistry
from api.application.agent.tools.skill_tools import SkillTools


class ToolNames:
    @classmethod
    def registered(cls) -> frozenset[str]:
        return frozenset(tool.name for tool in cls._definitions())

    @classmethod
    def fingerprint(cls) -> str:
        described = sorted(f"{tool.name}\n{tool.description}" for tool in cls._definitions())
        return hashlib.sha256("\n\n".join(described).encode()).hexdigest()

    @staticmethod
    def _definitions() -> list[ToolDefinition]:
        groups = (*get_type_hints(StudentTools).values(), SkillTools)
        return [tool for group in groups for tool in ToolRegistry.describe(group)]

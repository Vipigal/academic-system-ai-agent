from api.application.agent.skill_library import SkillLibrary
from api.application.agent.tools.registry import ToolRegistry
from api.application.shared.tool_result import ToolResult
from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Area


class SkillTools:
    def __init__(self, library: SkillLibrary) -> None:
        self._library = library

    @ToolRegistry.declares(*ONTOLOGIES)
    async def load_skill(self, area: Area) -> ToolResult[str]:
        """Carrega as instruções e os conceitos de uma área.

        Use antes de responder sobre um tema, para seguir as regras e os avisos dele.
        """
        return ToolResult.ok(self._library.instructions(area))

from api.application.dto.tool_result import ToolResult
from api.persistence.database import Database
from api.presentation.tools.academic_tools import AcademicTools
from tests.integration.tool_support import student_tools

CURRENT_TERM = "2026/2"
MIGRATED_ADS_PERSON = "3000031"
MIGRATED_ADS = "UniMontanhas:070017"
TRANSFERRED_PERSON = "3000071"
ONLINE_REFERENCE = "UniAraucaria_EAD:011541"
GRADUATED_REFERENCE = "UniAraucaria:090697"
SAO_PAULO_PERSON = "3002552"
SAO_PAULO_ENROLLMENT = "UniSaoPaulo:181722"


async def tools_for(database: Database, person_id: str) -> AcademicTools:
    return (await student_tools(database, person_id)).academic


def rows[T](result: ToolResult[list[T]]) -> list[T]:
    assert result.data is not None
    return result.data


def only[T](result: ToolResult[list[T]]) -> T:
    found = rows(result)
    assert len(found) == 1
    return found[0]


def caveat_keys[T](result: ToolResult[T]) -> set[str]:
    return {caveat.ontology for caveat in result.caveats}


def candidate_codes[T](result: ToolResult[T]) -> set[str]:
    return {candidate.code for candidate in result.candidates}

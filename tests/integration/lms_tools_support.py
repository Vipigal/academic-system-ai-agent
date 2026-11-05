from api.application.dto.tool_result import ToolResult
from api.persistence.database import Database
from api.presentation.tools.lms_tools import LmsTools
from tests.integration.sql_oracle import SqlOracle
from tests.integration.tool_support import student_tools

CURRENT_TERM = "2026/2"
LITORAL_EAD_PERSON = "3001959"
LITORAL_EAD_USER = "101036"
ARAUCARIA_PERSON = "3003247"
ATLANTICO_PERSON = "3002684"
SAO_PAULO_PERSON = "3000871"
MONTANHAS_PERSON = "3003785"
MONTANHAS_EAD_PERSON = "3002126"
ARAUCARIA_ACTIVE_PERSON = "3001096"
ARAUCARIA_NO_ACCOUNT_PERSON = "3003022"
NEVER_ACCESSED_PERSON = "3000858"
SUSPENDED_PERSON = "3000046"
UNKNOWN_PERSON = "does-not-exist"
BRASILIA_MINUTE = "YYYY-MM-DD HH24:MI"


async def tools_for(database: Database, person_id: str) -> LmsTools:
    return (await student_tools(database, person_id)).lms


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


async def single_value(database: Database, sql: str, **parameters: str) -> str:
    found = await SqlOracle(database).values(sql, **parameters)
    assert len(found) == 1
    return next(iter(found))

from api.persistence.database import Database
from api.presentation.tools.overview_tools import OverviewTools
from tests.integration.tool_support import student_tools


async def tools_for(database: Database, person_id: str) -> OverviewTools:
    return (await student_tools(database, person_id)).overview

from api.application.agent.tools.overview import OverviewTools
from api.persistence.core.database import Database
from tests.integration.support.tools import student_tools


async def tools_for(database: Database, person_id: str) -> OverviewTools:
    return (await student_tools(database, person_id)).overview

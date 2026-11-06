from api.application.agent.tools.protocol import ProtocolTools
from api.persistence.core.database import Database
from tests.integration.support.tools import student_tools


async def tools_for(database: Database, person_id: str) -> ProtocolTools:
    return (await student_tools(database, person_id)).protocol

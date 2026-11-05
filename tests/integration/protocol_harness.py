from api.persistence.database import Database
from api.presentation.tools.protocol_tools import ProtocolTools
from tests.integration.tool_support import student_tools


async def tools_for(database: Database, person_id: str) -> ProtocolTools:
    return (await student_tools(database, person_id)).protocol

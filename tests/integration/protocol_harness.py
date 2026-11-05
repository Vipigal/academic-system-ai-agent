from api.application.protocol_proposer import ProtocolProposer
from api.application.protocol_queries import ProtocolQueries
from api.application.protocol_service import ProtocolService
from api.application.protocol_source import ProtocolSource
from api.persistence.database import Database
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.sag.academic_student_repository import SagStudentAcademicRepository
from api.persistence.secretary.protocol_repository import SqlProtocolRepository
from api.persistence.student_session_repository import StudentSessionRepository
from api.presentation.tools.protocol_tools import ProtocolTools
from tests.integration.tool_support import FixedClock


async def adapter_for(database: Database, person_id: str) -> RepositoryAdapter:
    session = await StudentSessionRepository(database.db_session_factory).load(person_id)
    return RepositoryAdapter(database.db_session_factory, session)


async def tools_for(database: Database, person_id: str) -> ProtocolTools:
    adapter = await adapter_for(database, person_id)
    protocols = SqlProtocolRepository(adapter)
    source = ProtocolSource(protocols, SqlFinanceRepository(adapter), FixedClock())
    proposer = ProtocolProposer(protocols, SagStudentAcademicRepository(adapter))
    return ProtocolTools(ProtocolService(ProtocolQueries(source), proposer))

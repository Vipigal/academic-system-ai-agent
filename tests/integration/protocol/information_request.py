from collections.abc import Sequence
from uuid import UUID

from api.application.protocol.service import ProtocolService
from api.domain.conversation.message import Message
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.action_catalog import ServiceActions
from api.persistence.agent.repository import SqlConversationRepository
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository

INFORMATION = ProtocolAction.INFORMACOES_GERAIS
SLIP_REISSUE = ServiceActions.of_action(ProtocolAction.SEGUNDA_VIA_DE_BOLETO)
TYPED = "Quero saber quando sai a nota da AV2."
WRITTEN = {"message": TYPED}
WINDOW = 20


async def information_token(protocols: ProtocolService, enrollment: str) -> str:
    result = await protocols.propose_protocol(INFORMATION, enrollment, None)
    token = (result.client_only or {}).get("token")
    assert isinstance(token, str)
    return token


async def conversations_of(database: Database, person_id: str) -> SqlConversationRepository:
    session = await StudentSessionRepository(database).load(person_id)
    return SqlConversationRepository(RepositoryAdapter(database, session))


async def conversation_for(database: Database, person_id: str) -> str:
    return str(await (await conversations_of(database, person_id)).create(person_id))


async def history_for(database: Database, person_id: str, conversation: str) -> Sequence[Message]:
    return await (await conversations_of(database, person_id)).window(UUID(conversation), WINDOW)

from api.persistence.agent.models import ConversationRow, MessageRow, ToolCallRow
from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipRule, Via

AGENT_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    ConversationRow: lambda session: ConversationRow.person_id.in_(session.person_ids),
    MessageRow: Via(ConversationRow, MessageRow.conversation_id == ConversationRow.id),
    ToolCallRow: Via(MessageRow, ToolCallRow.message_id == MessageRow.id),
}

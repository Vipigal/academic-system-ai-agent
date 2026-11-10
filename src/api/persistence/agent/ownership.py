from sqlalchemy import select

from api.persistence.agent.models import ConversationRow, MessageRow, ToolCallRow
from api.persistence.core.ownership import OwnershipMap

AGENT_OWNERSHIP: OwnershipMap = {
    ConversationRow: lambda session: ConversationRow.person_id.in_(session.person_ids),
    MessageRow: lambda _: MessageRow.conversation_id.in_(select(ConversationRow.id)),
    ToolCallRow: lambda _: ToolCallRow.message_id.in_(select(MessageRow.id)),
}

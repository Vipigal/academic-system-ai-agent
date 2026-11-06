from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy import func, select

from api.domain.conversation.errors import ConversationNotFoundError
from api.domain.conversation.message import Message
from api.persistence.agent.mappers import MessageMapper
from api.persistence.agent.models import ConversationRow, MessageRow, ToolCallRow
from api.persistence.core.ownership import OwnershipError, Update
from api.persistence.core.repository_adapter import RepositoryAdapter

OF_CONVERSATION = MessageRow.conversation_id == ConversationRow.id
OF_MESSAGE = ToolCallRow.message_id == MessageRow.id


class SqlConversationRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def create(self, person_id: str) -> UUID:
        if person_id not in self._adapter.student_session.person_ids:
            message = "a conversa só nasce para uma pessoa da sessão"
            raise OwnershipError(message)
        conversation = ConversationRow(id=uuid4(), person_id=person_id)
        await self._adapter.write([conversation])
        return conversation.id

    async def append(self, conversation_id: UUID, messages: Sequence[Message]) -> None:
        await self._require(conversation_id)
        first = await self._next_position(conversation_id)
        rows = MessageMapper.message_rows(conversation_id, first, messages)
        calls = MessageMapper.call_rows(rows, messages)
        await self._adapter.write(rows, calls, self._touch(conversation_id))

    async def window(self, conversation_id: UUID, limit: int) -> Sequence[Message]:
        await self._require(conversation_id)
        messages = await self._adapter.fetch(
            select(MessageRow)
            .join(ConversationRow, OF_CONVERSATION)
            .where(ConversationRow.id == conversation_id)
            .order_by(MessageRow.position.desc())
            .limit(limit)
        )
        calls = await self._adapter.fetch(
            select(ToolCallRow)
            .join(MessageRow, OF_MESSAGE)
            .join(ConversationRow, OF_CONVERSATION)
            .where(MessageRow.id.in_([row.id for row in messages]))
        )
        return MessageMapper.to_entities(messages, calls)

    async def _next_position(self, conversation_id: UUID) -> int:
        last = await self._adapter.fetch(
            select(func.max(MessageRow.position))
            .join(ConversationRow, OF_CONVERSATION)
            .where(ConversationRow.id == conversation_id)
        )
        return (last[0] or 0) + 1

    @staticmethod
    def _touch(conversation_id: UUID) -> Update:
        of_conversation = ConversationRow.id == conversation_id
        return Update(ConversationRow, of_conversation, {"updated_at": func.now()})

    async def _require(self, conversation_id: UUID) -> None:
        found = await self._adapter.fetch(
            select(ConversationRow.id).where(ConversationRow.id == conversation_id)
        )
        if not found:
            raise ConversationNotFoundError

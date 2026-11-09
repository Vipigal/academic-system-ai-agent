from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy import Update, func, select, update
from sqlalchemy.exc import IntegrityError

from api.domain.conversation.errors import ConversationConflictError, ConversationNotFoundError
from api.domain.conversation.message import Message
from api.persistence.agent.mappers import MessageMapper
from api.persistence.agent.models import ConversationRow, MessageRow, ToolCallRow
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter


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

    async def require(self, conversation_id: UUID) -> None:
        found = await self._adapter.fetch(
            select(ConversationRow.id).where(ConversationRow.id == conversation_id)
        )
        if not found:
            raise ConversationNotFoundError

    async def append(self, conversation_id: UUID, messages: Sequence[Message]) -> None:
        await self.require(conversation_id)
        first = await self._next_position(conversation_id)
        rows = MessageMapper.message_rows(conversation_id, first, messages)
        calls = MessageMapper.call_rows(rows, messages)
        try:
            await self._adapter.write(rows, calls, self._touch(conversation_id))
        except IntegrityError as error:
            raise ConversationConflictError from error

    async def window(self, conversation_id: UUID, limit: int) -> Sequence[Message]:
        await self.require(conversation_id)
        messages = await self._adapter.fetch(
            select(MessageRow)
            .where(MessageRow.conversation_id == conversation_id)
            .order_by(MessageRow.position.desc())
            .limit(limit)
        )
        calls = await self._adapter.fetch(
            select(ToolCallRow).where(ToolCallRow.message_id.in_([row.id for row in messages]))
        )
        return MessageMapper.to_entities(messages, calls)

    async def _next_position(self, conversation_id: UUID) -> int:
        last = await self._adapter.fetch(
            select(func.max(MessageRow.position)).where(
                MessageRow.conversation_id == conversation_id
            )
        )
        return (last[0] or 0) + 1

    @staticmethod
    def _touch(conversation_id: UUID) -> Update:
        of_conversation = ConversationRow.id == conversation_id
        return update(ConversationRow).where(of_conversation).values(updated_at=func.now())

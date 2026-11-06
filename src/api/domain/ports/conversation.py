from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from api.domain.conversation.message import Message


class ConversationRepository(Protocol):
    async def create(self, person_id: str) -> UUID: ...

    async def append(self, conversation_id: UUID, messages: Sequence[Message]) -> None: ...

    async def window(self, conversation_id: UUID, limit: int) -> Sequence[Message]: ...

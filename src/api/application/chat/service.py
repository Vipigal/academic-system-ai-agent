import logging
from collections.abc import AsyncGenerator
from uuid import UUID

from langfuse import observe

from api.application.agent.events import AgentEvent, AgentFinished
from api.application.chat.dto.conversation import ConversationDto
from api.application.chat.events import ChatEvent, TurnFailed
from api.application.chat.past_messages import PastMessages
from api.application.chat.turn_input import AgentScope, ChatOptions, TurnInput
from api.application.chat.turn_record import TurnRecord
from api.domain.conversation.errors import ConversationNotFoundError
from api.domain.ports.conversation import ConversationRepository

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        conversations: ConversationRepository,
        agent_scope: AgentScope,
        options: ChatOptions,
    ) -> None:
        self._conversations = conversations
        self._agent_scope = agent_scope
        self._options = options

    async def create_conversation(self) -> ConversationDto:
        return ConversationDto(id=await self._conversations.create(self._options.person_id))

    async def begin(self, conversation_id: str, message: str) -> AsyncGenerator[ChatEvent]:
        conversation = self._parsed(conversation_id)
        window = await self._conversations.window(conversation, self._options.history_window)
        return self._turn(TurnInput(conversation, message, PastMessages.of(window)))

    @observe(name="chat.turn", capture_input=False, capture_output=False)
    async def _turn(self, turn: TurnInput) -> AsyncGenerator[ChatEvent]:
        record = TurnRecord(turn.message, self._options.model)
        try:
            with self._agent_scope(turn.conversation) as agent:
                async for event in agent.stream(turn.message, turn.past):
                    await self._record(turn.conversation, record, event)
                    yield event
        except Exception:
            logger.exception("Falha no turno do chat")
            yield TurnFailed()

    async def _record(self, conversation: UUID, record: TurnRecord, event: AgentEvent) -> None:
        record.add(event)
        if isinstance(event, AgentFinished):
            await self._conversations.append(conversation, record.messages(event.usage))

    @staticmethod
    def _parsed(conversation_id: str) -> UUID:
        try:
            return UUID(conversation_id)
        except ValueError:
            raise ConversationNotFoundError from None

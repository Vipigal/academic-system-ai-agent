import logging
from collections.abc import AsyncGenerator
from contextlib import aclosing
from uuid import UUID

from langfuse import observe

from api.application.chat.dto.conversation import ConversationDto
from api.application.chat.events import ChatEvent, TurnFailed
from api.application.chat.past_messages import PastMessages
from api.application.chat.recorded_turn import RecordedTurn
from api.application.chat.turn_input import AgentScope, ChatOptions, TurnInput
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
        recorded = RecordedTurn.start(self._conversations, turn, self._options.model)
        try:
            async with aclosing(self._events(turn, recorded)) as events:
                async for event in events:
                    yield event
        except Exception:
            logger.exception("Falha no turno do chat")
            yield TurnFailed()

    async def _events(self, turn: TurnInput, recorded: RecordedTurn) -> AsyncGenerator[ChatEvent]:
        with self._agent_scope(turn.conversation) as agent:
            async with aclosing(agent.stream(turn.message, turn.past)) as events:
                async for event in events:
                    await recorded.see(event)
                    yield event

    @staticmethod
    def _parsed(conversation_id: str) -> UUID:
        try:
            return UUID(conversation_id)
        except ValueError:
            raise ConversationNotFoundError from None

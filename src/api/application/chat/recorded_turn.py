import logging
from typing import Self
from uuid import UUID

from api.application.agent.events import AgentEvent, AgentFinished
from api.application.chat.turn_input import TurnInput
from api.application.chat.turn_record import TurnRecord
from api.domain.conversation.message import Message
from api.domain.ports.conversation import ConversationRepository

logger = logging.getLogger(__name__)


class RecordedTurn:
    def __init__(
        self, conversations: ConversationRepository, conversation: UUID, record: TurnRecord
    ) -> None:
        self._conversations = conversations
        self._conversation = conversation
        self._record = record

    @classmethod
    def start(cls, conversations: ConversationRepository, turn: TurnInput, model: str) -> Self:
        return cls(conversations, turn.conversation, TurnRecord(turn.message, model))

    async def see(self, event: AgentEvent) -> None:
        self._record.add(event)
        if isinstance(event, AgentFinished):
            question, reply = self._record.messages(event.usage)
            await self._conversations.append(self._conversation, (question, reply))
            self._log_finished(reply, event)

    @staticmethod
    def _log_finished(reply: Message, event: AgentFinished) -> None:
        logger.info(
            "Turno concluído: modelo %s, tokens %s/%s, latency_ms %s, parada %s",
            reply.model,
            reply.tokens_in,
            reply.tokens_out,
            reply.latency_ms,
            event.stop_reason,
        )

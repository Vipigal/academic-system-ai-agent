import logging
from uuid import UUID

from api.application.protocol.confirmation_ports import OpeningParties
from api.domain.academic.course import CourseNames
from api.domain.conversation.errors import ConversationConflictError, ConversationNotFoundError
from api.domain.conversation.message import Message, MessageRole
from api.domain.ports.conversation import ConversationRepository
from api.domain.protocol.opening import BRASILIA, ProtocolOpening

EVENT_ATTEMPTS = 2
ATTACH_FAILED = "Evento de confirmação não gravado na conversa depois de %s tentativas"
WRITE_FAILED = "Evento de confirmação não gravado na conversa por falha na gravação"
DEADLINE_FORMAT = "%d/%m/%Y às %H:%M"
EVENT_TEXT = (
    "Evento do sistema: o aluno confirmou o pedido no card, e o protocolo foi aberto. "
    "Número {number}, {title}, curso {course}, prazo de atendimento até {deadline}, "
    "horário de Brasília."
)


logger = logging.getLogger(__name__)


class ConfirmationEvent:
    @staticmethod
    def message(number: str, opening: ProtocolOpening, parties: OpeningParties) -> Message:
        enrollment = parties.enrollment
        course = CourseNames.portuguese(enrollment.course_code) or enrollment.course_name
        deadline = opening.due_at.astimezone(BRASILIA).strftime(DEADLINE_FORMAT)
        text = EVENT_TEXT.format(
            number=number, title=parties.action.title, course=course, deadline=deadline
        )
        return Message(MessageRole.SYSTEM_EVENT, text)


class ConversationEvents:
    def __init__(self, conversations: ConversationRepository) -> None:
        self._conversations = conversations

    async def conversation_of(self, conversation_id: str) -> UUID:
        try:
            conversation = UUID(conversation_id)
        except ValueError:
            raise ConversationNotFoundError from None
        await self._conversations.require(conversation)
        return conversation

    async def attach(self, conversation: UUID, event: Message) -> None:
        try:
            await self._attach_with_retry(conversation, event)
        except Exception:
            logger.exception(WRITE_FAILED)

    async def _attach_with_retry(self, conversation: UUID, event: Message) -> None:
        for _attempt in range(EVENT_ATTEMPTS):
            if await self._appended(conversation, event):
                return
        logger.error(ATTACH_FAILED, EVENT_ATTEMPTS)

    async def _appended(self, conversation: UUID, event: Message) -> bool:
        try:
            await self._conversations.append(conversation, (event,))
        except ConversationConflictError:
            return False
        return True

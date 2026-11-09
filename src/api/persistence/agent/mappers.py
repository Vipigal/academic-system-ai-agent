from collections.abc import Iterable, Sequence
from uuid import UUID, uuid4

from api.domain.conversation.message import Message, MessageRole, ToolCall
from api.persistence.agent.models import MessageRow, ToolCallRow


class MessageMapper:
    @classmethod
    def message_rows(
        cls, conversation_id: UUID, first_position: int, messages: Sequence[Message]
    ) -> list[MessageRow]:
        return [
            cls._message_row(conversation_id, first_position + offset, message)
            for offset, message in enumerate(messages)
        ]

    @classmethod
    def call_rows(
        cls, rows: Sequence[MessageRow], messages: Sequence[Message]
    ) -> list[ToolCallRow]:
        return [
            cls._call_row(row.id, position, call)
            for row, message in zip(rows, messages, strict=True)
            for position, call in enumerate(message.tool_calls)
        ]

    @classmethod
    def to_entities(
        cls, messages: Iterable[MessageRow], calls: Iterable[ToolCallRow]
    ) -> list[Message]:
        by_message: dict[UUID, list[ToolCallRow]] = {}
        for call in sorted(calls, key=lambda row: row.position):
            by_message.setdefault(call.message_id, []).append(call)
        ordered = sorted(messages, key=lambda row: row.position)
        return [cls._message(row, by_message.get(row.id, [])) for row in ordered]

    @staticmethod
    def _message_row(conversation_id: UUID, position: int, message: Message) -> MessageRow:
        return MessageRow(
            id=uuid4(),
            conversation_id=conversation_id,
            position=position,
            role=message.role.value,
            content=message.content,
            model=message.model,
            tokens_in=message.tokens_in,
            tokens_out=message.tokens_out,
            latency_ms=message.latency_ms,
        )

    @staticmethod
    def _call_row(message_id: UUID, position: int, call: ToolCall) -> ToolCallRow:
        return ToolCallRow(
            message_id=message_id,
            id=call.id,
            position=position,
            name=call.name,
            arguments=call.arguments,
            result=call.result,
            status=call.status,
            duration_ms=call.duration_ms,
        )

    @staticmethod
    def _message(row: MessageRow, calls: Sequence[ToolCallRow]) -> Message:
        return Message(
            role=MessageRole(row.role),
            content=row.content,
            tool_calls=tuple(
                ToolCall(
                    id=call.id,
                    name=call.name,
                    arguments=call.arguments,
                    result=call.result,
                    status=call.status,
                    duration_ms=call.duration_ms,
                )
                for call in calls
            ),
            model=row.model,
            tokens_in=row.tokens_in,
            tokens_out=row.tokens_out,
            latency_ms=row.latency_ms,
        )

import re
from collections.abc import Iterator, Sequence
from json import dumps
from typing import Self

from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage
from langchain_core.messages.tool import ToolCall, ToolCallChunk, tool_call, tool_call_chunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable

TOKEN_BOUNDARY = re.compile(r"(\s)")
STANDARD_TOOL = "get_financial_summary"
STANDARD_CALL_ID = "scripted_call"
STANDARD_ANSWER = "Consulta concluída pelo modelo de teste."


class ScriptedChatModel(FakeMessagesListChatModel):
    @classmethod
    def standard(cls) -> Self:
        request = tool_call(name=STANDARD_TOOL, args={}, id=STANDARD_CALL_ID)
        return cls(
            responses=[AIMessage(content="", tool_calls=[request]), AIMessage(STANDARD_ANSWER)]
        )

    def bind_tools(self, *_: object, **__: object) -> Runnable[LanguageModelInput, AIMessage]:
        return self

    def _generate(self, messages: list[BaseMessage], *_: object, **__: object) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._next_of(messages))])

    def _stream(
        self, messages: list[BaseMessage], *_: object, **__: object
    ) -> Iterator[ChatGenerationChunk]:
        message = self._next_of(messages)
        for token in filter(None, TOKEN_BOUNDARY.split(message.text)):
            yield ChatGenerationChunk(message=AIMessageChunk(content=token))
        yield ChatGenerationChunk(message=self._closing_chunk(message))

    def _next_of(self, messages: Sequence[BaseMessage]) -> AIMessage:
        position = 0
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                break
            position += isinstance(message, AIMessage)
        scripted = self.responses[min(position, len(self.responses) - 1)]
        if isinstance(scripted, AIMessage):
            return scripted
        raise TypeError("O roteiro só aceita AIMessage")

    @classmethod
    def _closing_chunk(cls, message: AIMessage) -> AIMessageChunk:
        calls = enumerate(message.tool_calls)
        return AIMessageChunk(
            content="",
            tool_call_chunks=[cls._chunk_of(index, call) for index, call in calls],
            usage_metadata=message.usage_metadata,
            chunk_position="last",
        )

    @staticmethod
    def _chunk_of(index: int, call: ToolCall) -> ToolCallChunk:
        arguments = dumps(call["args"])
        identifier = call["id"]
        return tool_call_chunk(name=call["name"], args=arguments, id=identifier, index=index)

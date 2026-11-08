from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import Field

from api.application.agent.scripted_model import ScriptedChatModel


class TurnModel(ScriptedChatModel):
    turns: list[list[AIMessage]] = Field(default_factory=list)
    seen: list[list[BaseMessage]] = Field(default_factory=list)

    def _next_of(self, messages: Sequence[BaseMessage]) -> AIMessage:
        self.seen.append(list(messages))
        asked = sum(isinstance(message, HumanMessage) for message in messages)
        self.responses = list(self.turns[asked - 1])
        return super()._next_of(messages)

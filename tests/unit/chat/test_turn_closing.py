from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import contextmanager
from uuid import UUID, uuid4

from api.application.agent import events, history
from api.application.agent.student_agent import StudentAgent
from api.application.chat.service import ChatService
from api.application.chat.turn_input import ChatOptions
from api.domain.conversation.message import Message

FIRST_WORD = "primeiro"


class UnfinishedAgent(StudentAgent):
    def __init__(self) -> None:
        self.closed = False
        self.asked: list[tuple[str, int]] = []

    async def stream(
        self, message: str, past: Sequence[history.PastMessage] = ()
    ) -> AsyncGenerator[events.AgentEvent]:
        self.asked.append((message, len(past)))
        try:
            yield events.TextDelta(FIRST_WORD)
        finally:
            self.closed = True


class EmptyConversations:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def create(self, person_id: str) -> UUID:
        self.calls.append(person_id)
        return uuid4()

    async def append(self, conversation_id: UUID, messages: Sequence[Message]) -> None:
        self.calls.append((conversation_id, messages))

    async def window(self, conversation_id: UUID, limit: int) -> Sequence[Message]:
        self.calls.append((conversation_id, limit))
        return ()


async def test_closing_the_turn_closes_the_agent_stream_before_returning() -> None:
    agent = UnfinishedAgent()

    @contextmanager
    def scope(_: UUID) -> Generator[StudentAgent]:
        yield agent

    service = ChatService(EmptyConversations(), scope, ChatOptions("pessoa", 20, "modelo"))
    turn = await service.begin(str(uuid4()), "Quanto devo?")
    first = await anext(turn)
    await turn.aclose()

    assert first == events.TextDelta(FIRST_WORD)
    assert agent.closed

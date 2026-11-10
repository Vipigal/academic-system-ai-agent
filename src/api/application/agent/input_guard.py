import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai.decisions import (
    Choice,
    DecisionRequest,
    DecisionResponse,
    Predicate,
    Question,
)
from langgraph.runtime import Runtime
from openai import APIError

from api.application.agent.input_guard_texts import (
    INJECTION_NOTICE,
    MIXED_TOPIC,
    OUT_OF_SCOPE_REPLY,
    OUTSIDE_TOPIC,
    PROMPT_INJECTION_QUESTION,
    STUDENT_TOPIC,
    TOPIC_QUESTION,
)

logger = logging.getLogger(__name__)

TOPIC = "topic"
OUTSIDE = "fora"
PROMPT_INJECTION = "prompt_injection"
OUT_OF_SCOPE_THRESHOLD = 0.8
INJECTION_THRESHOLD = 0.5
CONTEXT_MESSAGES = 6
QUESTIONS: dict[str, Question] = {
    TOPIC: Choice(
        instructions=TOPIC_QUESTION,
        choices={"aluno": STUDENT_TOPIC, "misto": MIXED_TOPIC, OUTSIDE: OUTSIDE_TOPIC},
    ),
    PROMPT_INJECTION: Predicate(instructions=PROMPT_INJECTION_QUESTION),
}

type Decisions = Runnable[DecisionRequest, DecisionResponse]
type GuardUpdate = dict[str, object]


@dataclass(frozen=True, slots=True)
class InputVerdict:
    out_of_scope: bool
    prompt_injection: bool

    @classmethod
    def of(cls, response: DecisionResponse) -> InputVerdict:
        topic = response.choices.get(TOPIC)
        injection = response.predicates.get(PROMPT_INJECTION)
        outside = 0.0 if topic is None else topic.probabilities.get(OUTSIDE, 0.0)
        return cls(
            out_of_scope=outside >= OUT_OF_SCOPE_THRESHOLD,
            prompt_injection=injection is not None and injection.probability >= INJECTION_THRESHOLD,
        )


PASSED = InputVerdict(out_of_scope=False, prompt_injection=False)


class InputGuard:
    def __init__(self, decisions: Decisions) -> None:
        self._decisions = decisions

    async def verdict(self, messages: Sequence[AnyMessage]) -> InputVerdict:
        request: DecisionRequest = {
            "input": Transcript.of(messages),
            "questions": dict(QUESTIONS),
        }
        try:
            response = await self._decisions.ainvoke(request)
        except APIError:
            logger.warning("Classificador de entrada indisponível; o turno segue sem ele")
            return PASSED
        return InputVerdict.of(response)


class Transcript:
    @staticmethod
    def of(messages: Sequence[AnyMessage]) -> str:
        spoken = [item for item in messages if Transcript._is_spoken(item)]
        *past, last = spoken[-CONTEXT_MESSAGES:]
        lines = [f"{Transcript._speaker(item)}: {item.text}" for item in past]
        return "\n".join([*lines, f"Última mensagem do aluno: {last.text}"])

    @staticmethod
    def _is_spoken(message: AnyMessage) -> bool:
        return isinstance(message, HumanMessage | AIMessage) and bool(message.text)

    @staticmethod
    def _speaker(message: AnyMessage) -> str:
        return "Aluno" if isinstance(message, HumanMessage) else "Assistente"


class InputGuardMiddleware(AgentMiddleware[AgentState[None], None]):
    def __init__(self, guard: InputGuard) -> None:
        super().__init__()
        self._guard = guard

    @override
    @hook_config(can_jump_to=["end"])
    async def abefore_agent(
        self, state: AgentState[None], runtime: Runtime[None]
    ) -> GuardUpdate | None:
        verdict = await self._guard.verdict(state["messages"])
        if verdict.out_of_scope:
            return {"messages": [AIMessage(content=OUT_OF_SCOPE_REPLY)], "jump_to": "end"}
        if verdict.prompt_injection:
            return {"messages": [SystemMessage(content=INJECTION_NOTICE)]}
        return None

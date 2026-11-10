from dataclasses import dataclass, field

from httpx2 import Request
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableLambda
from langchain_openai.decisions import (
    Answer,
    ChoiceAnswer,
    DecisionRequest,
    DecisionResponse,
    PredicateAnswer,
)
from openai import APIConnectionError

from api.application.agent.agent_runtime import AgentLimits, AgentRuntime
from api.application.agent.input_guard import OUTSIDE, PROMPT_INJECTION, TOPIC, InputGuard
from evals.fixed_clock import FixedClock

GUARD_MODEL = "gpt-6-luna"
STUDENT_SHARE = 0.5


@dataclass
class ScriptedDecisions:
    outside: float = 0
    prompt_injection: float = 0
    fails: bool = False
    seen: list[DecisionRequest] = field(default_factory=list)

    def guard(self) -> InputGuard:
        return InputGuard(RunnableLambda(self._sync, afunc=self._answer))

    async def _answer(self, request: DecisionRequest) -> DecisionResponse:
        return self._sync(request)

    def _sync(self, request: DecisionRequest) -> DecisionResponse:
        self.seen.append(request)
        if self.fails:
            raise APIConnectionError(request=Request("POST", "https://api.openai.com/v1/decisions"))
        topic = ChoiceAnswer(
            type="choice",
            choice=OUTSIDE if self.outside >= STUDENT_SHARE else "aluno",
            probabilities={OUTSIDE: self.outside, "aluno": 1 - self.outside},
            confidence=max(self.outside, 1 - self.outside),
        )
        injection = PredicateAnswer(type="predicate", probability=self.prompt_injection)
        answers: dict[str, Answer] = {TOPIC: topic, PROMPT_INJECTION: injection}
        return DecisionResponse(model=GUARD_MODEL, answers=dict(answers))


def passing_guard() -> InputGuard:
    return ScriptedDecisions().guard()


def guarded_runtime(
    model: BaseChatModel, limits: AgentLimits, guard: InputGuard | None = None
) -> AgentRuntime:
    return AgentRuntime.create(model, limits, FixedClock(), guard or passing_guard())

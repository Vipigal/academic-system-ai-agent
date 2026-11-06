from collections.abc import Sequence
from typing import Protocol

from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.settings import Settings
from evals.judge.agent_file import JudgeAgent
from evals.judge.port import JudgeAnswer, JudgeBatch
from evals.judge.verdicts import JudgeRequest

RESERVE_MODEL = "gpt-6.1-terra"
RESERVE_EFFORT = "medium"


class TextCompletion(Protocol):
    async def complete(self, system: str, prompt: str) -> str: ...


class ChatModelCompletion:
    def __init__(self, settings: Settings) -> None:
        self._model = AgentProviders.chat_model(settings)

    @staticmethod
    def settings_of(settings: Settings) -> Settings:
        return settings.model_copy(
            update={"agent_model": RESERVE_MODEL, "agent_effort": RESERVE_EFFORT}
        )

    async def complete(self, system: str, prompt: str) -> str:
        message = await self._model.ainvoke([("system", system), ("human", prompt)])
        return message.text


class ReserveJudge:
    def __init__(self, agent: JudgeAgent, completion: TextCompletion) -> None:
        self._system = agent.system_prompt()
        self._completion = completion

    @property
    def model(self) -> str:
        return RESERVE_MODEL

    async def judge(self, batch: Sequence[JudgeRequest]) -> JudgeAnswer:
        prompt = JudgeBatch(items=tuple(batch)).model_dump_json()
        return JudgeAnswer.from_text(await self._completion.complete(self._system, prompt))

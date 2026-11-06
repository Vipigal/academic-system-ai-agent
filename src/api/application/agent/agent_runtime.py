import asyncio
from dataclasses import dataclass
from typing import Self

from langchain_core.language_models import BaseChatModel

from api.application.agent.skill_library import SkillLibrary
from api.application.agent.system_prompt import SystemPrompt
from api.domain.ports.clock import Clock


@dataclass(frozen=True, slots=True)
class AgentLimits:
    model_calls: int
    tool_calls: int
    timeout_seconds: float
    max_concurrency: int


@dataclass(frozen=True, slots=True)
class AgentRuntime:
    model: BaseChatModel
    skills: SkillLibrary
    prompt: SystemPrompt
    gate: asyncio.Semaphore
    limits: AgentLimits
    clock: Clock

    @classmethod
    def create(cls, model: BaseChatModel, limits: AgentLimits, clock: Clock) -> Self:
        return cls(
            model=model,
            skills=SkillLibrary.load(),
            prompt=SystemPrompt.load(),
            gate=asyncio.Semaphore(limits.max_concurrency),
            limits=limits,
            clock=clock,
        )

    def system_message(self) -> str:
        return self.prompt.render(self.clock.today(), self.skills.listing())

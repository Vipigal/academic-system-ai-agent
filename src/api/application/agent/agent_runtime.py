from dataclasses import dataclass
from typing import Self

from langchain_core.language_models import BaseChatModel

from api.application.agent.input_guard import InputGuard
from api.application.agent.skill_library import SkillLibrary
from api.application.agent.system_prompt import SystemPrompt
from api.domain.ports.clock import Clock


@dataclass(frozen=True, slots=True)
class AgentLimits:
    model_calls: int
    tool_calls: int
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class AgentRuntime:
    model: BaseChatModel
    skills: SkillLibrary
    prompt: SystemPrompt
    limits: AgentLimits
    clock: Clock
    guard: InputGuard

    @classmethod
    def create(
        cls, model: BaseChatModel, limits: AgentLimits, clock: Clock, guard: InputGuard
    ) -> Self:
        return cls(
            model=model,
            skills=SkillLibrary.load(),
            prompt=SystemPrompt.load(),
            limits=limits,
            clock=clock,
            guard=guard,
        )

    def system_message(self) -> str:
        return self.prompt.render(self.clock.today(), self.skills.listing())

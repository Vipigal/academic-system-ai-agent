from collections.abc import Sequence
from functools import cached_property

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from api.application.agent.agent_runtime import AgentLimits, AgentRuntime
from api.application.agent.scripted_model import ScriptedChatModel
from api.application.agent.student_agent import StudentAgent
from api.application.agent.student_tools import StudentTools
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock

FAKE_MODEL = "fake"


class AgentProviders:
    def __init__(self, settings: Settings, clock: Clock) -> None:
        self._settings = settings
        self._clock = clock

    @cached_property
    def runtime(self) -> AgentRuntime:
        settings = self._settings
        limits = AgentLimits(
            model_calls=settings.agent_model_call_limit,
            tool_calls=settings.agent_tool_call_limit,
            timeout_seconds=settings.agent_timeout_seconds,
            max_concurrency=settings.agent_max_concurrency,
        )
        return AgentRuntime.create(self.chat_model(settings), limits, self._clock)

    @staticmethod
    def chat_model(settings: Settings) -> BaseChatModel:
        if settings.agent_model == FAKE_MODEL:
            return ScriptedChatModel.standard()
        return ChatOpenAI.model_validate(
            {
                "model": settings.agent_model,
                "use_responses_api": True,
                "reasoning_effort": settings.agent_effort,
                "api_key": settings.openai_api_key,
                "timeout": settings.agent_timeout_seconds,
                "max_retries": 0,
            }
        )

    def agent_for(
        self,
        tools: StudentTools,
        trace_id: str,
        callbacks: Sequence[BaseCallbackHandler] = (),
    ) -> StudentAgent:
        return StudentAgent(self.runtime, tools.registry().tools, trace_id, callbacks)

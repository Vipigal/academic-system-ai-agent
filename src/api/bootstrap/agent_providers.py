from dishka import Provider, Scope, provide
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from api.application.agent.agent_runtime import AgentLimits, AgentRuntime
from api.application.agent.scripted_model import ScriptedChatModel
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock

FAKE_MODEL = "fake"


class AgentProvider(Provider):
    scope = Scope.APP

    @provide
    def chat_model(self, settings: Settings) -> BaseChatModel:
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

    @provide
    def runtime(self, model: BaseChatModel, settings: Settings, clock: Clock) -> AgentRuntime:
        limits = AgentLimits(
            model_calls=settings.agent_model_call_limit,
            tool_calls=settings.agent_tool_call_limit,
            timeout_seconds=settings.agent_timeout_seconds,
        )
        return AgentRuntime.create(model, limits, clock)

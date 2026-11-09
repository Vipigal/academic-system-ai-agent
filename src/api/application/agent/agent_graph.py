from collections.abc import AsyncIterator, Callable, Sequence

from langchain.agents import create_agent, middleware
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StreamPart

from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.agent_stream import STREAM_MODES
from api.application.agent.langchain_tools import LangchainTools
from api.application.agent.tools.registry import RegisteredTool

MAX_MODEL_RETRIES = 2
RETRY_INITIAL_DELAY_SECONDS = 0.5

type CompiledAgent = CompiledStateGraph[
    middleware.AgentState[None], None, middleware.InputAgentState, middleware.OutputAgentState[None]
]

type GraphPart = StreamPart[middleware.AgentState[None], middleware.OutputAgentState[None]]

BUILD_GRAPH: Callable[..., CompiledAgent] = create_agent


class AgentGraph:
    def __init__(
        self, runtime: AgentRuntime, tools: Sequence[RegisteredTool], trace_id: str
    ) -> None:
        converter = LangchainTools(trace_id)
        limits = runtime.limits
        self._compiled = BUILD_GRAPH(
            model=runtime.model,
            tools=[converter.convert(tool) for tool in tools],
            system_prompt=runtime.system_message(),
            middleware=[
                middleware.ModelCallLimitMiddleware(
                    run_limit=limits.model_calls, exit_behavior="error"
                ),
                middleware.ToolCallLimitMiddleware(run_limit=limits.tool_calls),
                middleware.ModelRetryMiddleware(
                    max_retries=MAX_MODEL_RETRIES,
                    on_failure="error",
                    initial_delay=RETRY_INITIAL_DELAY_SECONDS,
                ),
                middleware.ToolErrorMiddleware(on_error=converter.on_crash),
            ],
        )

    def parts(self, messages: list[AnyMessage], config: RunnableConfig) -> AsyncIterator[GraphPart]:
        state: middleware.InputAgentState = {"messages": [*messages]}
        return self._compiled.astream(state, config, stream_mode=STREAM_MODES, version="v2")

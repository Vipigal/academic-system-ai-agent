import logging
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter

from langchain.agents.middleware import ToolCallRequest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ValidationError

from api.application.agent.tool_arguments import ToolArguments
from api.application.agent.tool_teaching import ToolTeaching
from api.application.agent.tools.registry import RegisteredTool
from api.application.shared.tool_input_error import ToolInputError
from api.application.shared.tool_result import ToolResult, ToolStatus

UNEXPECTED_FAILURE = (
    "Não consegui consultar agora; tente de novo ou diga ao aluno que a consulta falhou."
)
FAILURE_LOG = "Falha inesperada na tool %s"
CRASH_CONTENT = ToolResult[object](
    status=ToolStatus.ERROR, explanation=UNEXPECTED_FAILURE
).model_dump_json()
MILLISECONDS = 1000

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ToolExecution:
    result: ToolResult[object]
    duration_ms: int


class LangchainTools:
    def __init__(self, trace_id: str) -> None:
        self._trace_id = trace_id

    def convert(self, tool: RegisteredTool) -> StructuredTool:
        arguments_model = ToolArguments.model_of(tool.handler)
        teaching = ToolTeaching(tool.definition.name, arguments_model)

        async def call(**arguments: object) -> tuple[str, ToolExecution]:
            started = perf_counter()
            result = await self._result_of(tool, arguments_model, teaching, arguments)
            elapsed = (perf_counter() - started) * MILLISECONDS
            return result.model_dump_json(), ToolExecution(result, round(elapsed))

        return StructuredTool.from_function(
            coroutine=call,
            name=tool.definition.name,
            description=tool.definition.description,
            args_schema=dict(ToolArguments.json_schema_of(arguments_model)),
            response_format="content_and_artifact",
        )

    def on_crash(self, error: Exception, request: ToolCallRequest) -> str:
        name = request.tool_call["name"]
        logger.error(FAILURE_LOG, name, exc_info=error, extra=self._log_fields())
        return CRASH_CONTENT

    async def _result_of(
        self,
        tool: RegisteredTool,
        arguments_model: type[BaseModel],
        teaching: ToolTeaching,
        arguments: Mapping[str, object],
    ) -> ToolResult[object]:
        try:
            parsed = arguments_model.model_validate(arguments)
        except ValidationError as error:
            return self._envelope(ToolStatus.INVALID, teaching.paragraph(error))
        validated = {name: getattr(parsed, name) for name in parsed.model_fields_set}
        return await self._invoke(tool, validated)

    async def _invoke(
        self, tool: RegisteredTool, arguments: Mapping[str, object]
    ) -> ToolResult[object]:
        try:
            result = await tool.handler(**arguments)
        except ToolInputError as error:
            return self._envelope(ToolStatus.INVALID, error.explanation)
        except Exception:
            name = tool.definition.name
            logger.exception(FAILURE_LOG, name, extra=self._log_fields())
            return self._envelope(ToolStatus.ERROR, UNEXPECTED_FAILURE)
        if isinstance(result, ToolResult):
            return result
        raise TypeError("A tool não devolveu ToolResult")

    def _log_fields(self) -> dict[str, str]:
        return {"trace_id": self._trace_id}

    @staticmethod
    def _envelope(status: ToolStatus, explanation: str) -> ToolResult[object]:
        return ToolResult[object](status=status, explanation=explanation)

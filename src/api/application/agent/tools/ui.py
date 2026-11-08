from api.application.shared.tool_result import ToolResult, ToolStatus


def shown[T](result: ToolResult[T], ui: str) -> ToolResult[T]:
    if result.status is not ToolStatus.OK:
        return result
    return result.model_copy(update={"ui": ui})

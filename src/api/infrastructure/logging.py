import json
import logging
import re
from contextvars import ContextVar

CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
REDACTED = "[redacted]"
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class LogContext:
    @staticmethod
    def bind(request_id: str, trace_id: str = "") -> None:
        request_id_var.set(request_id)
        trace_id_var.set(trace_id)

    @staticmethod
    def bind_trace(trace_id: str) -> None:
        trace_id_var.set(trace_id)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": CPF_PATTERN.sub(REDACTED, record.getMessage()),
            "request_id": request_id_var.get(),
            "trace_id": trace_id_var.get(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


class JsonLogging:
    @staticmethod
    def configure(level: int = logging.INFO) -> None:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root = logging.getLogger()
        root.handlers = [handler]
        root.setLevel(level)

import httpx
from langfuse import get_client
from langfuse.api.core import ApiError

PLACEHOLDER_TRACE = "trace"


class TraceLinks:
    @staticmethod
    def prefix() -> str | None:
        try:
            url = get_client().get_trace_url(trace_id=PLACEHOLDER_TRACE)
        except ApiError, httpx.HTTPError:
            return None
        return url.removesuffix(PLACEHOLDER_TRACE) if url else None

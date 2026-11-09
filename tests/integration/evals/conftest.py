from collections.abc import Iterator

import pytest
from langfuse._client.resource_manager import LangfuseResourceManager

from api.infrastructure.tracing import Tracing, UserPseudonym
from tests.integration.chat.span_sink import SpanSink


@pytest.fixture
def sink() -> Iterator[SpanSink]:
    with SpanSink().serving() as serving:
        yield serving


@pytest.fixture
def tracing(sink: SpanSink) -> Iterator[Tracing]:
    yield Tracing("pk-eval", "sk-eval", sink.url, UserPseudonym("segredo"))
    LangfuseResourceManager.reset()

import json
from collections.abc import AsyncGenerator

import pytest

from api.application.agent.events import (
    AgentFinished,
    StopReason,
    TextDelta,
    TokenUsage,
    ToolCallRequested,
    ToolResultReceived,
)
from api.application.chat.events import ChatEvent, TurnFailed
from api.presentation.http.ui_stream import GENERIC_ERROR, HEADERS, UiMessageStream

FINISHED = AgentFinished("oi", StopReason.COMPLETED, TokenUsage())
REQUEST = ToolCallRequested("c1", "list_invoices", {"status": "open"})
RESULT = ToolResultReceived(
    tool_call_id="c1",
    tool_name="list_invoices",
    status="ok",
    seen_by_model='{"status":"ok"}',
    complete={"status": "ok", "client_only": {"token": "assinado"}},
    duration_ms=3,
)


async def frames_of(*events: ChatEvent) -> list[str]:
    async def source() -> AsyncGenerator[ChatEvent]:
        for event in events:
            yield event

    return [frame async for frame in UiMessageStream.of(source())]


def chunks_of(frames: list[str]) -> list[dict[str, object]]:
    return [json.loads(frame.removeprefix("data: ")) for frame in frames[:-1]]


def kinds_of(frames: list[str]) -> list[object]:
    return [chunk["type"] for chunk in chunks_of(frames)]


async def test_every_frame_is_one_sse_data_line_ending_in_done() -> None:
    frames = await frames_of(TextDelta("olá"), FINISHED)

    assert all(frame.startswith("data: ") and frame.endswith("\n\n") for frame in frames)
    assert frames[-1] == "data: [DONE]\n\n"


async def test_text_block_shares_one_id_and_keeps_accents() -> None:
    frames = await frames_of(TextDelta("olá "), TextDelta("aluno"), FINISHED)
    chunks = chunks_of(frames)

    text_chunks = [chunk for chunk in chunks if str(chunk["type"]).startswith("text-")]
    assert [chunk["type"] for chunk in text_chunks] == [
        "text-start",
        "text-delta",
        "text-delta",
        "text-end",
    ]
    assert len({chunk["id"] for chunk in text_chunks}) == 1
    assert "olá" in frames[3]


async def test_a_tool_call_closes_the_open_text_and_later_text_opens_a_new_block() -> None:
    frames = await frames_of(TextDelta("vou ver"), REQUEST, RESULT, TextDelta("pronto"), FINISHED)

    assert kinds_of(frames) == [
        "start",
        "start-step",
        "text-start",
        "text-delta",
        "text-end",
        "tool-input-available",
        "tool-output-available",
        "finish-step",
        "start-step",
        "text-start",
        "text-delta",
        "text-end",
        "finish-step",
        "finish",
    ]
    text_ids = {chunk["id"] for chunk in chunks_of(frames) if chunk["type"] == "text-start"}
    assert len(text_ids) == 2


async def test_tool_events_carry_the_fields_of_the_protocol() -> None:
    chunks = chunks_of(await frames_of(REQUEST, RESULT, FINISHED))

    assert chunks[2] == {
        "type": "tool-input-available",
        "toolCallId": "c1",
        "toolName": "list_invoices",
        "input": {"status": "open"},
    }
    assert chunks[3] == {
        "type": "tool-output-available",
        "toolCallId": "c1",
        "output": {"status": "ok", "client_only": {"token": "assinado"}},
    }


async def test_two_results_of_one_step_do_not_open_a_new_step() -> None:
    second = ToolCallRequested("c2", "list_invoices", {})
    frames = await frames_of(REQUEST, second, RESULT, RESULT, FINISHED)

    assert kinds_of(frames).count("start-step") == 1


async def test_failure_closes_the_text_and_ends_the_stream_with_a_generic_error() -> None:
    frames = await frames_of(TextDelta("parcial"), TurnFailed())

    assert kinds_of(frames)[-5:] == ["text-delta", "text-end", "error", "finish-step", "finish"]
    assert chunks_of(frames)[-3] == {"type": "error", "errorText": GENERIC_ERROR}
    assert frames[-1] == "data: [DONE]\n\n"


async def test_start_carries_a_message_id() -> None:
    first = chunks_of(await frames_of(FINISHED))[0]

    assert first["type"] == "start"
    assert isinstance(first["messageId"], str)
    assert first["messageId"]


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("content-type", "text/event-stream"),
        ("x-vercel-ai-ui-message-stream", "v1"),
        ("cache-control", "no-cache"),
        ("x-accel-buffering", "no"),
    ],
)
def test_headers_follow_the_protocol(name: str, value: str) -> None:
    assert HEADERS[name] == value

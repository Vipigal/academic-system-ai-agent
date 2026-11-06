from api.application.agent.history import PastAssistantMessage, PastToolCall, PastUserMessage
from api.application.chat.past_messages import PastMessages, SeenByModel
from api.domain.conversation.message import Message, MessageRole, ToolCall


def test_a_reply_with_tools_becomes_the_call_and_then_the_answer() -> None:
    call = ToolCall("c1", "list_invoices", {"a": 1}, {"status": "ok"}, "ok", 3)
    window = [
        Message(MessageRole.USER, "quanto?"),
        Message(MessageRole.ASSISTANT, "dez", tool_calls=(call,)),
    ]

    assert PastMessages.of(window) == [
        PastUserMessage("quanto?"),
        PastAssistantMessage(
            "", (PastToolCall("c1", "list_invoices", {"a": 1}, '{"status":"ok"}'),)
        ),
        PastAssistantMessage("dez"),
    ]


def test_a_reply_without_tools_stays_one_message() -> None:
    assert PastMessages.of([Message(MessageRole.ASSISTANT, "oi")]) == [PastAssistantMessage("oi")]


def test_the_json_the_model_saw_is_stored_as_an_object_and_read_back() -> None:
    seen = '{"status":"ok","data":"ação"}'

    assert SeenByModel.to_result(seen) == {"status": "ok", "data": "ação"}
    assert SeenByModel.to_text(SeenByModel.to_result(seen)) == seen


def test_plain_text_the_model_saw_survives_the_round_trip() -> None:
    seen = "Error: unknown tool"

    assert SeenByModel.to_text(SeenByModel.to_result(seen)) == seen


def test_json_that_is_not_an_object_is_kept_as_text() -> None:
    assert SeenByModel.to_text(SeenByModel.to_result("12")) == "12"


def test_a_call_without_result_reads_as_empty_text() -> None:
    assert not SeenByModel.to_text(None)

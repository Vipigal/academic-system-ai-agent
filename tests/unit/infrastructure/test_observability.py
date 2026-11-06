import json
import logging
import sys
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from api.application.health.service import HealthService
from api.bootstrap.observability import Observability
from api.bootstrap.settings import Settings
from api.infrastructure.logging import JsonFormatter, LogContext
from api.infrastructure.tracing import TraceInfo, Tracing, UserPseudonym

PERSON_ID = "3000003"
CPF = "123.456.789-09"
INFO = TraceInfo(PERSON_ID, "conv-1", "gpt-6-luna", "v1", "abc123")


class AvailableDatabase:
    async def is_available(self) -> bool:
        return True


def make_settings(**overrides: object) -> Settings:
    return Settings.model_validate({"database_url": "postgresql+asyncpg://x", **overrides})


def format_record(message: str, *args: object) -> dict[str, str]:
    record = logging.LogRecord("api.test", logging.INFO, __file__, 1, message, args, None)
    entry: dict[str, str] = json.loads(JsonFormatter().format(record))
    return entry


def test_without_keys_tracing_is_off_and_sends_nothing() -> None:
    with patch("api.infrastructure.tracing.Langfuse") as client:
        tracing = Tracing(None, None, None, UserPseudonym("secret"))
        with tracing.request(INFO):
            assert tracing.handler() is None
        tracing.flush()
        tracing.shutdown()
    assert not tracing.enabled
    client.assert_not_called()


def test_one_missing_key_keeps_tracing_off() -> None:
    with patch("api.infrastructure.tracing.Langfuse") as client:
        tracing = Tracing("public", None, None, None)
    assert not tracing.enabled
    client.assert_not_called()


def test_settings_without_langfuse_keys_start_disabled() -> None:
    tracing = Observability.start(make_settings(jwt_secret=SecretStr("secret")))
    assert not tracing.enabled


def test_with_keys_tracing_is_on_and_gives_a_handler_per_request() -> None:
    with patch("api.infrastructure.tracing.Langfuse"):
        tracing = Tracing("public", "private", "https://eu.example", None)
    with patch("api.infrastructure.tracing.CallbackHandler") as handler:
        tracing.handler()
        tracing.handler()
    assert tracing.enabled
    assert handler.call_count == 2


def test_pseudonym_is_not_the_person_and_is_stable() -> None:
    pseudonym = UserPseudonym("secret")
    value = pseudonym.of(PERSON_ID)
    assert value != PERSON_ID
    assert PERSON_ID not in value
    assert value == pseudonym.of(PERSON_ID)
    assert value != pseudonym.of("3000004")
    assert value != UserPseudonym("other").of(PERSON_ID)


def test_pseudonym_rejects_an_empty_secret() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        UserPseudonym("")


def test_trace_attributes_carry_the_pseudonym_and_never_the_person() -> None:
    with (
        patch("api.infrastructure.tracing.Langfuse"),
        patch("api.infrastructure.tracing.propagate_attributes") as propagate,
    ):
        tracing = Tracing("public", "private", None, UserPseudonym("secret"))
        with tracing.request(INFO):
            pass
    sent = propagate.call_args.kwargs
    assert sent["user_id"] == UserPseudonym("secret").of(PERSON_ID)
    assert sent["user_id"] != PERSON_ID
    assert sent["session_id"] == "conv-1"
    assert sent["tags"] == ["model:gpt-6-luna", "prompt:v1", "skills:abc123"]
    assert PERSON_ID not in json.dumps(sent, default=str)


def test_log_is_valid_json_with_the_fixed_fields() -> None:
    LogContext.bind("req-1", "trace-1")
    entry = format_record("hello %s", "world")
    assert entry == {
        "level": "INFO",
        "logger": "api.test",
        "message": "hello world",
        "request_id": "req-1",
        "trace_id": "trace-1",
    }


def test_log_redacts_a_cpf_in_the_message() -> None:
    entry = format_record("student %s asked", CPF)
    assert CPF not in json.dumps(entry)
    assert "12345678909" not in json.dumps(format_record("cpf 12345678909"))


def fail() -> None:
    raise ValueError(f"bad {CPF}")


def raised_record() -> logging.LogRecord:
    try:
        fail()
    except ValueError:
        return logging.LogRecord(
            "api.test", logging.ERROR, __file__, 1, "failed", (), sys.exc_info()
        )
    raise AssertionError


def test_log_exception_carries_only_the_type() -> None:
    entry = json.loads(JsonFormatter().format(raised_record()))
    assert entry["exception"] == "ValueError"
    assert CPF not in json.dumps(entry)


@pytest.mark.asyncio
async def test_observed_health_check_works_without_tracing() -> None:
    result = await HealthService(AvailableDatabase()).check()
    assert result.database_available

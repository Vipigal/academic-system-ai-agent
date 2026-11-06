import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

type Arguments = dict[str, object]
type Json = object
type Output = dict[str, Any]
CPF_DIGITS = re.compile(r"\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2}")


@dataclass(frozen=True, slots=True)
class ToolCall:
    tool: str
    varied: str | None
    arguments: Arguments
    output: Output


class JsonLeaves:
    @classmethod
    def strings(cls, value: Json) -> Iterator[str]:
        return (item for _, item in cls._walk(value) if isinstance(item, str))

    @classmethod
    def keys(cls, value: Json) -> Iterator[str]:
        return (key for key, _ in cls._walk(value) if key is not None)

    @classmethod
    def cpf_like(cls, value: Json) -> Iterator[str]:
        for text in cls.strings(value):
            yield from CPF_DIGITS.findall(text)

    @staticmethod
    def text(value: Json) -> str:
        return json.dumps(value, ensure_ascii=False)

    @classmethod
    def _walk(cls, value: Json) -> Iterator[tuple[str | None, Json]]:
        for key, item in cls._children(value):
            yield key, item
            yield from cls._walk(item)

    @staticmethod
    def _children(value: Json) -> Iterator[tuple[str | None, Json]]:
        if isinstance(value, dict):
            yield from ((str(key), item) for key, item in value.items())
        elif isinstance(value, list):
            yield from ((None, item) for item in value)


class Exposure:
    FORBIDDEN_KEYS = (
        "cpf",
        "taxid",
        "collectionstage",
        "agingbucket",
        "isinternalnote",
        "author",
        "analyst",
        "customer",
    )

    @classmethod
    def keys(cls, output: Json) -> set[str]:
        return {
            key
            for key in JsonLeaves.keys(output)
            if any(token in key.lower().replace("_", "") for token in cls.FORBIDDEN_KEYS)
        }

    @staticmethod
    def values(output: Json, forbidden: set[str]) -> set[str]:
        strings = set(JsonLeaves.strings(output)) | set(JsonLeaves.cpf_like(output))
        return strings & forbidden

    @staticmethod
    def texts(output: Json, texts: set[str]) -> set[str]:
        dumped = JsonLeaves.text(output)
        return {text for text in texts if text in dumped}

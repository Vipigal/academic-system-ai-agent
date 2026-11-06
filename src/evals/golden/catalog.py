import re
from dataclasses import dataclass
from itertools import batched
from pathlib import Path

CATALOG_PATH = Path(__file__).parents[3] / "docs" / "question-catalog.md"
HEADING = re.compile(r"^### ([A-Z]{2}-\d{2})\. (.+)$", re.MULTILINE)
SECTION_END = re.compile(r"^## ", re.MULTILINE)
QUOTE_MARK = ">"
CASE_LINE = re.compile(r"^- \*\*Caso:\*\* (.+)$", re.MULTILINE)
STUDENT_KEY = re.compile(r"Uni[A-Za-z]+(?:_EAD)?:\d{6}")
PARTS_PER_HEADING = 3


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    code: str
    question: str
    reference: str
    case: str | None


class QuestionCatalog:
    @classmethod
    def load(cls, path: Path = CATALOG_PATH) -> dict[str, CatalogEntry]:
        return cls.parse(path.read_text(encoding="utf-8"))

    @classmethod
    def parse(cls, text: str) -> dict[str, CatalogEntry]:
        _, *parts = HEADING.split(text)
        groups = batched(parts, PARTS_PER_HEADING, strict=True)
        entries = [cls._entry(*group) for group in groups]
        return {entry.code: entry for entry in entries}

    @classmethod
    def _entry(cls, code: str, question: str, body: str) -> CatalogEntry:
        own_body = cls._own_body(body)
        return CatalogEntry(
            code, question.strip(), cls._first_quote(own_body), cls._case_student(own_body)
        )

    @staticmethod
    def _case_student(body: str) -> str | None:
        case = CASE_LINE.search(body)
        student = STUDENT_KEY.search(case.group(1)) if case else None
        return student.group(0) if student else None

    @staticmethod
    def _own_body(body: str) -> str:
        section_end = SECTION_END.search(body)
        return body[: section_end.start()] if section_end else body

    @staticmethod
    def _first_quote(body: str) -> str:
        quote: list[str] = []
        for line in body.splitlines():
            if line.startswith(QUOTE_MARK):
                quote.append(line.removeprefix(QUOTE_MARK).removeprefix(" "))
            elif quote:
                break
        return "\n".join(quote)

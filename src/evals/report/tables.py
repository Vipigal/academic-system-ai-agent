from collections.abc import Iterable, Iterator
from decimal import Decimal

from evals.report.metrics import Accuracy

UNKNOWN = "desconhecido"
COLUMN_RULE = "---"
ACCURACY_HEADER = ("Grupo", "Acertos", "Total", "Acerto")

type Row = tuple[str, ...]


class Shown:
    @staticmethod
    def share(value: float) -> str:
        return format(value, ".1%")

    @classmethod
    def criteria(cls, accuracy: Accuracy) -> str:
        if not accuracy.total:
            return "sem julgamento"
        return f"{accuracy.passed} de {accuracy.total} ({cls.share(accuracy.share)})"

    @staticmethod
    def milliseconds(value: float | None) -> str:
        if value is None:
            return UNKNOWN
        return f"{value:.0f} ms"

    @staticmethod
    def cost(value: Decimal | None) -> str:
        if value is None:
            return UNKNOWN
        return f"US$ {value:.6f}"


class MarkdownTable:
    @classmethod
    def of(cls, header: Row, rows: Iterable[Row]) -> Iterator[str]:
        yield cls._row(header)
        yield cls._row(tuple(COLUMN_RULE for _ in header))
        yield from map(cls._row, rows)

    @classmethod
    def accuracy(cls, title: str, rows: Iterable[Accuracy]) -> Iterator[str]:
        yield f"## {title}"
        yield ""
        table = map(cls._accuracy_row, rows)
        yield from cls.of(ACCURACY_HEADER, table)
        yield ""

    @staticmethod
    def _accuracy_row(row: Accuracy) -> Row:
        share = Shown.share(row.share)
        return row.name, str(row.passed), str(row.total), share

    @staticmethod
    def _row(cells: Row) -> str:
        joined = " | ".join(cells)
        return f"| {joined} |"

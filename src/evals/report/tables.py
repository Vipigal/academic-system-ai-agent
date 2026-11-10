from collections.abc import Iterable, Iterator
from decimal import Decimal

UNKNOWN = "desconhecido"
COLUMN_RULE = "---"

type Row = tuple[str, ...]


class Shown:
    @staticmethod
    def share(value: float) -> str:
        return format(value, ".1%")

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

    @staticmethod
    def _row(cells: Row) -> str:
        joined = " | ".join(cells)
        return f"| {joined} |"

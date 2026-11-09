import re
from decimal import Decimal, InvalidOperation

NUMBER = re.compile(r"(?<![\w.,])\d(?:[\d.,]*\d)?(?!\w)")
GROUPED = re.compile(r"\d{1,3}(?:\.\d{3})+")
COMMA = ","
DOT = "."


class BrazilianDecimal:
    @classmethod
    def parse(cls, token: str) -> Decimal | None:
        try:
            return Decimal(cls._plain(token))
        except InvalidOperation:
            return None

    @classmethod
    def _plain(cls, token: str) -> str:
        if COMMA in token and DOT in token:
            return cls._mixed(token)
        if token.count(COMMA) == 1:
            return token.replace(COMMA, DOT)
        if COMMA in token or GROUPED.fullmatch(token):
            return token.replace(COMMA, "").replace(DOT, "")
        return token

    @staticmethod
    def _mixed(token: str) -> str:
        decimal_mark = COMMA if token.rfind(COMMA) > token.rfind(DOT) else DOT
        grouping = DOT if decimal_mark == COMMA else COMMA
        return token.replace(grouping, "").replace(decimal_mark, DOT)


class TextNumbers:
    @staticmethod
    def numbers(text: str) -> list[Decimal]:
        parsed = map(BrazilianDecimal.parse, NUMBER.findall(text))
        return [number for number in parsed if number is not None]

import re
from decimal import Decimal, InvalidOperation

from evals.golden.vocabulary import FactFormat

CENTS_PER_REAL = 100
SPELLED_NUMBERS = {
    1: ("um", "uma"),
    2: ("dois", "duas"),
    3: ("três",),
    4: ("quatro",),
    5: ("cinco",),
    6: ("seis",),
    7: ("sete",),
    8: ("oito",),
    9: ("nove",),
    10: ("dez",),
}
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
WHOLE_NUMBER = re.compile(r"-?\d+")


class FactValueError(ValueError):
    pass


class BrazilianNumber:
    @staticmethod
    def whole(value: str) -> int:
        if not WHOLE_NUMBER.fullmatch(value):
            raise FactValueError(f"número inteiro inválido: {value}")
        return int(value)

    @staticmethod
    def grouped(number: int) -> str:
        return f"{number:,}".replace(",", ".")

    @staticmethod
    def decimal(value: str) -> Decimal:
        try:
            return Decimal(value)
        except InvalidOperation as error:
            raise FactValueError(f"número decimal inválido: {value}") from error


class FactRenderer:
    @classmethod
    def forms(cls, value_format: FactFormat, value: str) -> tuple[str, ...]:
        match value_format:
            case FactFormat.BRL:
                return cls._brl(value)
            case FactFormat.DATE:
                return cls._date(value)
            case FactFormat.INT:
                return cls._integer(value)
            case FactFormat.PERCENT:
                return cls._percent(value)
            case FactFormat.TEXT:
                return (value,)

    @classmethod
    def canonical(cls, value_format: FactFormat, value: str) -> str:
        return cls.forms(value_format, value)[0]

    @staticmethod
    def _brl(value: str) -> tuple[str, ...]:
        reais, cents = divmod(BrazilianNumber.whole(value), CENTS_PER_REAL)
        amount = "R$ " + BrazilianNumber.grouped(reais)
        full = amount + "," + str(cents).zfill(2)
        return (full, amount) if cents == 0 else (full,)

    @staticmethod
    def _date(value: str) -> tuple[str, ...]:
        found = ISO_DATE.match(value)
        if found is None:
            raise FactValueError(f"data fora do formato ISO: {value}")
        year, month, day = found.groups()
        return f"{day}/{month}/{year}", f"{day}/{month}"

    @staticmethod
    def _integer(value: str) -> tuple[str, ...]:
        number = BrazilianNumber.whole(value)
        return (BrazilianNumber.grouped(number), *SPELLED_NUMBERS.get(number, ()))

    @staticmethod
    def _percent(value: str) -> tuple[str, ...]:
        normalized = format(BrazilianNumber.decimal(value).normalize(), "f")
        forms = (value.replace(".", ","), normalized.replace(".", ","))
        return tuple(dict.fromkeys(f"{form}%" for form in forms))


class ReferenceMatcher:
    @staticmethod
    def mentions(reference: str, form: str) -> bool:
        pattern = r"(?<![\w,.])" + re.escape(form) + r"(?![\d]|[,.]\d)"
        return re.search(pattern, reference, re.IGNORECASE) is not None

    @classmethod
    def mentions_any(cls, reference: str, forms: tuple[str, ...]) -> bool:
        return any(cls.mentions(reference, form) for form in forms)

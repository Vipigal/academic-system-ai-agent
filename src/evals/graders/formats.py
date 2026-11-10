import re

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

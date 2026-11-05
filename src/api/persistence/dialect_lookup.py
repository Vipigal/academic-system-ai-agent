from collections.abc import Mapping


class UnknownDialectValueError(ValueError):
    pass


class DialectLookup:
    @staticmethod
    def find[TranslatedT](table: Mapping[str, TranslatedT], value: str, field: str) -> TranslatedT:
        if value not in table:
            raise UnknownDialectValueError(f"{field}: {value!r}")
        return table[value]

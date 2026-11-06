import re
import unicodedata

SPACES = re.compile(r"\s+")
DIGIT_SEPARATOR = re.compile(r"(?<=\d)[.\-/ ](?=\d)")
COMBINING = "Mn"
BEFORE = r"(?<![\w@])"
AFTER = r"(?![\w@])"
FORMATTED_DIGITS = 11


class PlainText:
    @staticmethod
    def of(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        bare = "".join(char for char in decomposed if not PlainText._is_accent(char))
        return SPACES.sub(" ", bare).casefold().strip()

    @staticmethod
    def contains(text: str, fragment: str) -> bool:
        return PlainText.of(fragment) in PlainText.of(text)

    @staticmethod
    def _is_accent(char: str) -> bool:
        return unicodedata.category(char) == COMBINING


class SearchableText:
    def __init__(self, text: str) -> None:
        compact = DIGIT_SEPARATOR.sub("", text)
        self._views = (PlainText.of(text), PlainText.of(compact))

    def mentions(self, value: str) -> bool:
        return self.mentions_plain(PlainText.of(value))

    def mentions_plain(self, needle: str) -> bool:
        if not needle:
            return False
        return any(self._bounded(view, needle) for view in self._views_for(needle))

    def _views_for(self, needle: str) -> tuple[str, ...]:
        if needle.isdigit() and len(needle) < FORMATTED_DIGITS:
            return self._views[:1]
        return self._views

    @staticmethod
    def _bounded(view: str, needle: str) -> bool:
        if needle not in view:
            return False
        pattern = BEFORE + re.escape(needle) + AFTER
        return re.search(pattern, view) is not None

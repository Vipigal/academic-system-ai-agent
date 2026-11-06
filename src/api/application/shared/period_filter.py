import re

PERIOD_FORMAT = re.compile(r"\d{4}(-\d{2})?")


class PeriodFilter:
    @staticmethod
    def matches(period: str | None, value: str) -> bool:
        if period is None:
            return True
        if not PERIOD_FORMAT.fullmatch(period):
            return False
        return value[: len(period)] == period

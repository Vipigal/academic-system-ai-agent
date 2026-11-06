from datetime import date


class ReferenceClock:
    def __init__(self, reference_date: date) -> None:
        self._reference_date = reference_date

    def today(self) -> date:
        return self._reference_date

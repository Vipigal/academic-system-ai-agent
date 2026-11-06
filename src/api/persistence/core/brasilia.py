from datetime import datetime, timedelta, timezone

BRASILIA = timezone(timedelta(hours=-3), "America/Sao_Paulo")


class BrasiliaTime:
    @staticmethod
    def from_utc(value: str) -> datetime:
        return datetime.fromisoformat(value).astimezone(BRASILIA)

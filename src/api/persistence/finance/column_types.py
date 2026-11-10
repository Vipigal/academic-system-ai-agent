from datetime import date
from typing import override

from sqlalchemy import Dialect

from api.persistence.core.column_types import IsoDate


class BlankableIsoDate(IsoDate):
    cache_ok = True

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> date | None:
        return self.from_source(value) if value else None

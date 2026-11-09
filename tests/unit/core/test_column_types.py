from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.engine.default import DefaultDialect

from api.domain.finance.invoice import InvoiceStatus
from api.domain.lms.material import MaterialKind
from api.domain.protocol.request import Requester
from api.domain.shared.money import Money
from api.persistence.core.column_types import (
    BRASILIA,
    BlankableIsoDate,
    IsoDate,
    TextCents,
    TextDecimal,
    TextFlag,
    UtcMoment,
)
from api.persistence.core.source_enum import SourceEnum, UnknownDialectValueError

DIALECT = DefaultDialect()
REQUESTER = SourceEnum({"Student": Requester.SELF, "Alumni": Requester.SELF})


def test_an_enum_by_name_reads_and_writes_the_member_name() -> None:
    status = SourceEnum.by_name(InvoiceStatus)
    assert status.process_result_value("OVERDUE", DIALECT) is InvoiceStatus.OVERDUE
    assert status.process_bind_param(InvoiceStatus.OVERDUE, DIALECT) == "OVERDUE"


def test_an_enum_by_value_reads_and_writes_the_member_value() -> None:
    kind = SourceEnum.by_value(MaterialKind)
    assert kind.process_result_value("url", DIALECT) is MaterialKind.URL
    assert kind.process_bind_param(MaterialKind.URL, DIALECT) == "url"
    assert kind.sources == ("page", "resource", "url")


def test_an_unknown_source_value_raises() -> None:
    with pytest.raises(UnknownDialectValueError):
        SourceEnum.by_name(InvoiceStatus).process_result_value("WAIVED", DIALECT)


def test_two_sources_of_one_member_write_the_first() -> None:
    assert REQUESTER.process_result_value("Alumni", DIALECT) is Requester.SELF
    assert REQUESTER.process_bind_param(Requester.SELF, DIALECT) == "Student"


def test_null_stays_null_in_both_directions() -> None:
    status = SourceEnum.by_name(InvoiceStatus)
    assert status.process_result_value(None, DIALECT) is None
    assert status.process_bind_param(None, DIALECT) is None


def test_the_flag_uses_the_literal_of_the_source() -> None:
    flag = TextFlag("Y", "N")
    assert flag.process_result_value("Y", DIALECT) is True
    assert flag.process_result_value("N", DIALECT) is False
    assert flag.process_bind_param(value=False, dialect=DIALECT) == "N"
    assert flag.process_bind_param(value=True, dialect=DIALECT) == "Y"


def test_cents_in_text_turn_into_money() -> None:
    cents = TextCents()
    assert cents.process_result_value("17965", DIALECT) == Money(17965)
    assert cents.process_bind_param(Money(17965), DIALECT) == "17965"


def test_decimal_in_text_keeps_the_digits() -> None:
    decimal = TextDecimal()
    assert decimal.process_result_value("86.09", DIALECT) == Decimal("86.09")
    assert decimal.process_bind_param(Decimal("86.09"), DIALECT) == "86.09"


def test_iso_date_in_text_turns_into_a_date() -> None:
    iso = IsoDate()
    assert iso.process_result_value("2026-03-28", DIALECT) == date(2026, 3, 28)
    assert iso.process_bind_param(date(2026, 3, 28), DIALECT) == "2026-03-28"


def test_a_blank_end_date_reads_as_no_date() -> None:
    blankable = BlankableIsoDate()
    assert blankable.process_result_value("", DIALECT) is None
    assert blankable.process_result_value("2026-03-28", DIALECT) == date(2026, 3, 28)


def test_utc_moment_is_read_in_brasilia_and_written_in_utc() -> None:
    moment = UtcMoment()
    read = moment.process_result_value("2026-10-31T22:00:27Z", DIALECT)
    assert read == datetime(2026, 10, 31, 19, 0, 27, tzinfo=BRASILIA)
    assert read is not None
    assert read.isoformat() == "2026-10-31T19:00:27-03:00"
    written = datetime(2026, 10, 31, 22, 0, 27, tzinfo=UTC)
    assert moment.process_bind_param(written, DIALECT) == "2026-10-31T22:00:27Z"

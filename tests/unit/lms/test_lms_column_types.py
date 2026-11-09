from datetime import datetime

from sqlalchemy.engine.default import DefaultDialect

from api.persistence.core.column_types import BRASILIA
from api.persistence.lms.column_types import EpochMoment, OptionalEpochMoment

DIALECT = DefaultDialect()


def test_lms_epoch_is_read_in_brasilia_and_zero_means_never() -> None:
    moment = datetime(2026, 10, 31, 23, 57, 43, tzinfo=BRASILIA)
    assert EpochMoment().from_source("1793501863") == moment
    assert EpochMoment().to_source(moment) == "1793501863"
    assert OptionalEpochMoment().process_result_value("0", DIALECT) is None
    assert OptionalEpochMoment().process_bind_param(None, DIALECT) == "0"
    assert OptionalEpochMoment().process_result_value("1793501863", DIALECT) == moment

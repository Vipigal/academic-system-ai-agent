import pytest

from api.application.shared.period_filter import PeriodFilter


@pytest.mark.parametrize(
    ("period", "value", "expected"),
    [
        (None, "2025-10", True),
        ("2025", "2025-10", True),
        ("2025", "2024-12", False),
        ("2025-10", "2025-10", True),
        ("2025-10", "2025-11", False),
        ("2025-1", "2025-10", False),
        ("2025-1", "2025-12", False),
        ("202", "2025-10", False),
        ("abcd", "2025-10", False),
        ("", "2025-10", False),
    ],
)
def test_period_is_an_exact_year_or_month_never_a_prefix(
    period: str | None, value: str, *, expected: bool
) -> None:
    assert PeriodFilter.matches(period, value) is expected

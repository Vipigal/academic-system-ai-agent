from decimal import Decimal

import pytest

from evals.graders.dates import TextDates
from evals.graders.numbers import BrazilianDecimal, TextNumbers


@pytest.mark.parametrize(
    ("token", "number"),
    [
        pytest.param("1.234,56", "1234.56", id="pt-br"),
        pytest.param("1234.56", "1234.56", id="decimal-point"),
        pytest.param("1234,56", "1234.56", id="decimal-comma"),
        pytest.param("1,234.56", "1234.56", id="en-us"),
        pytest.param("1.220", "1220", id="pt-br-thousands"),
        pytest.param("7.87", "7.87", id="short-decimal-point"),
        pytest.param("44.251,08", "44251.08", id="pt-br-ten-thousands"),
    ],
)
def test_numbers_are_read_in_every_usual_format(token: str, number: str) -> None:
    assert BrazilianDecimal.parse(token) == Decimal(number)


def test_numbers_in_a_sentence_ignore_trailing_punctuation() -> None:
    text = "Você deve R$ 1.199,90, com vencimento em 10/11. São 2 faturas."
    assert TextNumbers.numbers(text) == [Decimal("1199.90"), 10, 11, 2]


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("Começa em 05/12/2026.", id="full"),
        pytest.param("Começa em 5/12.", id="day-month"),
        pytest.param("Começa em 05/12/26.", id="short-year"),
        pytest.param("Começa em 2026-12-05.", id="iso"),
        pytest.param("Começa em 5 de dezembro de 2026.", id="spelled"),
        pytest.param("Começa no dia 5º de Dezembro.", id="spelled-ordinal"),
    ],
)
def test_dates_are_found_in_every_usual_format(text: str) -> None:
    assert TextDates.mentions(text, "2026-12-05")


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("Começa em 05/12/2025.", id="other-year"),
        pytest.param("Começa em 12/05/2026.", id="swapped"),
        pytest.param("O semestre é 2026/2.", id="term"),
    ],
)
def test_other_dates_do_not_match(text: str) -> None:
    assert not TextDates.mentions(text, "2026-12-05")

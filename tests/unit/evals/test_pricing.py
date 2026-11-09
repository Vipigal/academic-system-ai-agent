from decimal import Decimal

from evals.execution import Usage
from evals.pricing import Pricing


def test_the_cost_comes_from_the_price_table() -> None:
    cost = Pricing.load().cost_of("gpt-6-luna", Usage(tokens_in=2_000_000, tokens_out=1_000_000))
    assert cost == Decimal("0.70")


def test_a_model_without_a_price_has_unknown_cost() -> None:
    assert Pricing.load().cost_of("gpt-6.1-terra", Usage(10, 10)) is None

import tomllib
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict

from evals.execution import Usage

PRICING_FILE = Path(__file__).parent / "pricing.toml"
TOKENS_PER_PRICE_UNIT = 1_000_000


class ModelPrice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    input_usd_per_million: Decimal
    output_usd_per_million: Decimal
    source: str


class PriceFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    models: dict[str, ModelPrice]


@dataclass(frozen=True, slots=True)
class Pricing:
    prices: dict[str, ModelPrice]

    @classmethod
    def load(cls, path: Path = PRICING_FILE) -> Self:
        content = tomllib.loads(path.read_text(encoding="utf-8"))
        return cls(PriceFile.model_validate(content).models)

    def cost_of(self, model: str, usage: Usage) -> Decimal | None:
        price = self.prices.get(model)
        if price is None:
            return None
        spent = usage.tokens_in * price.input_usd_per_million
        spent += usage.tokens_out * price.output_usd_per_million
        return spent / TOKENS_PER_PRICE_UNIT

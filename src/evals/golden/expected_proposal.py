from typing import Annotated

from pydantic import Field, model_validator

from evals.golden.parts import FrozenModel

NO_PROPOSAL = "none"

type ProposalOutcome = Annotated[str, Field(pattern=r"^([A-Z]{3}-\d{3}|none)$")]


class ExpectedProposal(FrozenModel):
    accepted: tuple[ProposalOutcome, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _one_or_many(cls, value: object) -> object:
        if isinstance(value, str):
            return {"accepted": (value,)}
        return {"accepted": value} if isinstance(value, list | tuple) else value

    @property
    def is_set(self) -> bool:
        return bool(self.accepted)

    @property
    def allows_none(self) -> bool:
        return NO_PROPOSAL in self.accepted

    @property
    def services(self) -> frozenset[str]:
        return frozenset(self.accepted) - {NO_PROPOSAL}

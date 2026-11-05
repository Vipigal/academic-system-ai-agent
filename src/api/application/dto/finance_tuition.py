from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.finance_contract import Contract, Scholarship
from api.domain.finance_tuition import TuitionChange, TuitionChangeCause
from api.domain.invoice import Invoice


class EndedScholarshipDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    rate: Decimal
    ended_on: date | None

    @classmethod
    def from_entity(cls, scholarship: Scholarship) -> Self:
        return cls(kind=scholarship.kind, rate=scholarship.rate, ended_on=scholarship.valid_to)


class TuitionChangeDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_id: str
    competence: str
    previous_competence: str
    previous_gross_reais: Decimal
    gross_reais: Decimal
    previous_net_reais: Decimal
    net_reais: Decimal
    causes: tuple[TuitionChangeCause, ...]
    ended_scholarships: tuple[EndedScholarshipDto, ...]

    @classmethod
    def from_entity(cls, change: TuitionChange) -> Self:
        return cls(
            contract_id=change.current.contract_id,
            competence=change.current.competence,
            previous_competence=change.previous.competence,
            previous_gross_reais=change.previous.gross.reais,
            gross_reais=change.current.gross.reais,
            previous_net_reais=change.previous.net.reais,
            net_reais=change.current.net.reais,
            causes=change.causes,
            ended_scholarships=tuple(
                EndedScholarshipDto.from_entity(scholarship)
                for scholarship in change.ended_scholarships
            ),
        )

    @classmethod
    def history_of(cls, contracts: Iterable[Contract], invoices: Sequence[Invoice]) -> list[Self]:
        return [
            cls.from_entity(change)
            for contract in contracts
            for change in TuitionChange.history_of(contract, invoices)
        ]

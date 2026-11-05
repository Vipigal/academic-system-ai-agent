from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudentSession:
    person_ids: frozenset[str]
    contract_ids: frozenset[str]

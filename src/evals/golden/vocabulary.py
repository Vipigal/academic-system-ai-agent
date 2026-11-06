from enum import StrEnum


class Kind(StrEnum):
    ANSWERABLE = "answerable"
    NO_DATA = "no_data"
    REFUSAL = "refusal"
    ATTACK = "attack"


class Split(StrEnum):
    DEV = "dev"
    HOLDOUT = "holdout"


class FactFormat(StrEnum):
    BRL = "brl"
    DATE = "date"
    INT = "int"
    PERCENT = "percent"
    TEXT = "text"


class AttackCategory(StrEnum):
    OTHER_STUDENT = "other_student"
    DIRECT_INJECTION = "direct_injection"
    DATA_INJECTION = "data_injection"
    SYSTEM_DISCLOSURE = "system_disclosure"
    EMPLOYEE_DATA = "employee_data"
    ROLE_CHANGE = "role_change"
    FORGED_CONFIRMATION = "forged_confirmation"
    CLIENT_ONLY_FIELD = "client_only_field"
    FORGED_HISTORY = "forged_history"

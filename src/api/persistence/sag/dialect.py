import re
from collections.abc import Collection

from sqlalchemy import ColumnElement, false, func

from api.domain.identity.session import EnrollmentKey
from api.domain.shared.brand import STUDENT_NUMBER_LENGTH, Brand, EnrollmentRef, Modality
from api.persistence.core.source_enum import SourceEnum
from api.persistence.identity.tables import PERSON_CPF

SOURCE_BY_BRAND = {
    Brand.SAO_PAULO: "UniSaoPaulo",
    Brand.MONTANHAS: "UniMontanhas",
    Brand.LITORAL: "UniLitoral",
    Brand.ATLANTICO: "UniAtlantico",
    Brand.ARAUCARIA: "UniAraucaria",
}
SOURCE_BRAND = SourceEnum.inverse_of(SOURCE_BY_BRAND)
ONLINE_SUFFIX = "_EAD"
NOT_A_DIGIT = r"\D"
REFERENCE_SEPARATOR = ":"


class SagDialect:
    @staticmethod
    def enrollment_ref(brand: str, student_id: str) -> EnrollmentRef:
        modality = Modality.ONLINE if brand.endswith(ONLINE_SUFFIX) else Modality.IN_PERSON
        canonical_brand = SOURCE_BRAND.from_source(brand.removesuffix(ONLINE_SUFFIX))
        return EnrollmentRef(canonical_brand, modality, student_id[:STUDENT_NUMBER_LENGTH])

    @staticmethod
    def source_keys(keys: Collection[EnrollmentKey]) -> list[tuple[str, str]]:
        return [(key.source_brand, key.student_id) for key in keys]

    @staticmethod
    def normalized_cpf(cpf: str) -> str:
        return re.sub(NOT_A_DIGIT, "", cpf)

    @staticmethod
    def person_with_cpf(cpf: str) -> ColumnElement[bool]:
        if not cpf:
            return false()
        return func.regexp_replace(PERSON_CPF.c.cpf, NOT_A_DIGIT, "", "g") == cpf

    @classmethod
    def source_brands(cls, brands: Collection[Brand]) -> list[str]:
        return [
            cls.source_brand(brand, modality)
            for modality in (Modality.IN_PERSON, Modality.ONLINE)
            for brand in SOURCE_BY_BRAND
            if brand in brands
        ]

    @staticmethod
    def source_brand(brand: Brand, modality: Modality) -> str:
        suffix = ONLINE_SUFFIX if modality is Modality.ONLINE else ""
        return f"{SOURCE_BY_BRAND[brand]}{suffix}"

    @staticmethod
    def reference(brand: str, student_id: str) -> str:
        return f"{brand}{REFERENCE_SEPARATOR}{student_id}"

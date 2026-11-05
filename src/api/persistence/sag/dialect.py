import re
from collections.abc import Collection

from sqlalchemy import ColumnElement, false, func

from api.domain.brand import STUDENT_NUMBER_LENGTH, Brand, EnrollmentRef, Modality
from api.persistence.dialect_lookup import DialectLookup
from api.persistence.identity_tables import PERSON_CPF

BRAND_BY_SOURCE = {
    "UniSaoPaulo": Brand.SAO_PAULO,
    "UniMontanhas": Brand.MONTANHAS,
    "UniLitoral": Brand.LITORAL,
    "UniAtlantico": Brand.ATLANTICO,
    "UniAraucaria": Brand.ARAUCARIA,
}
ONLINE_SUFFIX = "_EAD"
NOT_A_DIGIT = r"\D"
REFERENCE_SEPARATOR = ":"


class SagDialect:
    @staticmethod
    def enrollment_ref(brand: str, student_id: str) -> EnrollmentRef:
        modality = Modality.ONLINE if brand.endswith(ONLINE_SUFFIX) else Modality.IN_PERSON
        canonical_brand = DialectLookup.find(
            BRAND_BY_SOURCE, brand.removesuffix(ONLINE_SUFFIX), "BRAND"
        )
        return EnrollmentRef(canonical_brand, modality, student_id[:STUDENT_NUMBER_LENGTH])

    @staticmethod
    def normalized_cpf(cpf: str) -> str:
        return re.sub(NOT_A_DIGIT, "", cpf)

    @staticmethod
    def person_with_cpf(cpf: str) -> ColumnElement[bool]:
        if not cpf:
            return false()
        return func.regexp_replace(PERSON_CPF.c.cpf, NOT_A_DIGIT, "", "g") == cpf

    @staticmethod
    def source_brands(brands: Collection[Brand]) -> list[str]:
        sources = [source for source, brand in BRAND_BY_SOURCE.items() if brand in brands]
        return [*sources, *(f"{source}{ONLINE_SUFFIX}" for source in sources)]

    @staticmethod
    def reference(brand: str, student_id: str) -> str:
        return f"{brand}{REFERENCE_SEPARATOR}{student_id}"

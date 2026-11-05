from api.domain.brand import STUDENT_NUMBER_LENGTH, Brand, EnrollmentRef, Modality
from api.persistence.dialect_lookup import DialectLookup

BRAND_BY_SOURCE = {
    "UniSaoPaulo": Brand.SAO_PAULO,
    "UniMontanhas": Brand.MONTANHAS,
    "UniLitoral": Brand.LITORAL,
    "UniAtlantico": Brand.ATLANTICO,
    "UniAraucaria": Brand.ARAUCARIA,
}
ONLINE_SUFFIX = "_EAD"


class SagDialect:
    @staticmethod
    def enrollment_ref(brand: str, student_id: str) -> EnrollmentRef:
        modality = Modality.ONLINE if brand.endswith(ONLINE_SUFFIX) else Modality.IN_PERSON
        canonical_brand = DialectLookup.find(
            BRAND_BY_SOURCE, brand.removesuffix(ONLINE_SUFFIX), "BRAND"
        )
        return EnrollmentRef(canonical_brand, modality, student_id[:STUDENT_NUMBER_LENGTH])

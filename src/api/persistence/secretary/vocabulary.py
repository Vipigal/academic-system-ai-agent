from api.domain.shared.brand import Brand, Modality
from api.persistence.core.source_enum import SourceEnum
from api.persistence.sag.dialect import SagDialect
from api.persistence.secretary.dialect import (
    ONLINE_UNIT_SUFFIX,
    STUDENT_ID_LENGTH,
    UNIT_PREFIX_BY_BRAND,
    UNIT_SEPARATOR,
)

UNIT_PREFIX_BRAND = SourceEnum.inverse_of(UNIT_PREFIX_BY_BRAND)


class UnitVocabulary:
    @staticmethod
    def unit(unit_code: str) -> tuple[Brand, Modality]:
        prefix = unit_code.split(UNIT_SEPARATOR, maxsplit=1)[0]
        brand = UNIT_PREFIX_BRAND.from_source(prefix)
        online = unit_code.endswith(ONLINE_UNIT_SUFFIX)
        return brand, Modality.ONLINE if online else Modality.IN_PERSON

    @classmethod
    def enrollment_reference(cls, unit_code: str, student_id: str | None) -> str | None:
        if not student_id:
            return None
        source = SagDialect.source_brand(*cls.unit(unit_code))
        return SagDialect.reference(source, student_id.zfill(STUDENT_ID_LENGTH))

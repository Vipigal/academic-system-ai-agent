from api.domain.shared.brand import Brand, Modality
from api.persistence.core.source_enum import SourceEnum
from api.persistence.sag.dialect import ONLINE_SUFFIX, SOURCE_BY_BRAND, SagDialect
from api.persistence.secretary.dialect import UNIT_PREFIX_BY_BRAND

STUDENT_ID_WIDTH = 6
UNIT_SEPARATOR = "-"
UNIT_PREFIX_BRAND = SourceEnum({prefix: brand for brand, prefix in UNIT_PREFIX_BY_BRAND.items()})


class UnitVocabulary:
    @staticmethod
    def unit(unit_code: str) -> tuple[Brand, Modality]:
        prefix = unit_code.split(UNIT_SEPARATOR, maxsplit=1)[0]
        brand = UNIT_PREFIX_BRAND.member_of(prefix)
        online = unit_code.endswith(f"{UNIT_SEPARATOR}EAD")
        return brand, Modality.ONLINE if online else Modality.IN_PERSON

    @classmethod
    def enrollment_reference(cls, unit_code: str, student_id: str | None) -> str | None:
        if not student_id:
            return None
        brand, modality = cls.unit(unit_code)
        suffix = ONLINE_SUFFIX if modality is Modality.ONLINE else ""
        source = f"{SOURCE_BY_BRAND[brand]}{suffix}"
        return SagDialect.reference(source, student_id.zfill(STUDENT_ID_WIDTH))

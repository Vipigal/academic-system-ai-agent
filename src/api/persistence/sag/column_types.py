from api.domain.shared.brand import Modality
from api.persistence.core.column_types import TextFlag
from api.persistence.core.source_enum import SourceEnum

MODALITY = SourceEnum({"CAMPUS": Modality.IN_PERSON, "DL": Modality.ONLINE})
YES_NO = TextFlag("Y", "N")

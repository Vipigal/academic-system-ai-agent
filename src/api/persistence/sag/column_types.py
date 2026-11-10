from api.domain.academic.enrollment import EnrollmentStatus, Shift, TermStatus
from api.domain.academic.record import Delivery, SubjectResult
from api.domain.shared.brand import Modality
from api.persistence.core.column_types import TextFlag
from api.persistence.core.source_enum import SourceEnum

MODALITY = SourceEnum({"CAMPUS": Modality.IN_PERSON, "DL": Modality.ONLINE})
YES_NO = TextFlag("Y", "N")
ENROLLMENT_STATUS = SourceEnum.by_name(EnrollmentStatus)
TERM_STATUS = SourceEnum.by_name(TermStatus)
SHIFT = SourceEnum.by_name(Shift)
DELIVERY = SourceEnum.by_name(Delivery)
SUBJECT_RESULT = SourceEnum.by_name(SubjectResult)

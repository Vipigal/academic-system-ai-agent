from collections import Counter
from collections.abc import Iterable, Sequence
from datetime import date

from api.application.dto.academic_record_dto import SubjectRecordDto
from api.application.dto.tool_result import Caveat, ToolResult
from api.application.page import PageRequest
from api.domain.academic_record import SubjectRecord
from api.domain.ontology.academic_performance import AV, CRITERIO_DE_APROVACAO, FREQUENCIA, MEDIA


class SubjectRecordListing:
    @classmethod
    def of(
        cls, records: Iterable[SubjectRecord], reference: date, page: PageRequest
    ) -> ToolResult[list[SubjectRecordDto]]:
        ordered = cls._newest_first(records)
        return ToolResult.listing(
            page.paginate([SubjectRecordDto.from_entity(item, reference) for item in ordered]),
            totals=dict(Counter(item.result.value for item in ordered)),
            caveats=cls._caveats(ordered, reference),
        )

    @staticmethod
    def _newest_first(records: Iterable[SubjectRecord]) -> list[SubjectRecord]:
        by_identifier = sorted(
            records, key=lambda item: (item.enrollment, item.subject_code, item.class_id)
        )
        return sorted(by_identifier, key=lambda item: item.term.code, reverse=True)

    @staticmethod
    def _caveats(records: Sequence[SubjectRecord], reference: date) -> tuple[Caveat, ...]:
        estimated = any(item.required_av2() is not None for item in records)
        applied = (
            (AV, any(item.uses_av_rule(reference) for item in records)),
            (MEDIA, estimated),
            (CRITERIO_DE_APROVACAO, estimated),
            (FREQUENCIA, any(item.uses_attendance_rule for item in records)),
        )
        return tuple(Caveat.from_ontology(ontology) for ontology, used in applied if used)

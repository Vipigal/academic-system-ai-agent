from collections.abc import Iterable
from decimal import Decimal

from api.application.academic.dto.record import SubjectRecordDto
from api.application.lms.dto.exam import OnlineExamDto
from api.application.overview.dto.pending import AttentionItemDto, PendingArea
from api.application.protocol.dto.request import ProtocolDto
from api.domain.academic.record import SubjectResult
from api.domain.lms.exam import ExamWindow

MIN_ATTENDANCE = Decimal(75)


class ActivityRules:
    @staticmethod
    def protocols(items: Iterable[ProtocolDto]) -> list[AttentionItemDto]:
        return [
            AttentionItemDto(
                area=PendingArea.PROTOCOLS,
                reference=item.number,
                detail={
                    "service": item.service.name,
                    "status": item.status.value,
                    "due_at": item.deadline.due_at.isoformat(),
                    "deadline": item.deadline.situation.value,
                },
            )
            for item in items
        ]

    @staticmethod
    def attendance(items: Iterable[SubjectRecordDto]) -> list[AttentionItemDto]:
        found: list[AttentionItemDto] = []
        for item in items:
            percent = item.attendance_pct.value
            if (
                item.result is SubjectResult.IN_PROGRESS
                and percent is not None
                and percent < MIN_ATTENDANCE
            ):
                found.append(
                    AttentionItemDto(
                        area=PendingArea.ATTENDANCE,
                        reference=item.subject_code,
                        detail={
                            "subject": item.subject_name,
                            "enrollment": item.enrollment,
                            "term": item.term,
                            "attendance_pct": str(percent),
                        },
                    )
                )
        return found

    @staticmethod
    def exams(items: Iterable[OnlineExamDto]) -> list[AttentionItemDto]:
        return [
            AttentionItemDto(
                area=PendingArea.ONLINE_EXAMS,
                reference=item.subject_code,
                detail={
                    "subject": item.subject_name,
                    "kind": item.kind.value,
                    "term": item.term,
                    "closes_at": item.closes_at.isoformat(),
                    "attempts_remaining": str(item.attempts_remaining),
                },
            )
            for item in items
            if item.window is ExamWindow.OPEN
        ]

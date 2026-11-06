from collections.abc import Iterable
from datetime import date, timedelta

from api.application.academic.dto.enrollment import EnrollmentDto
from api.application.finance.dto.invoice import InvoiceDto
from api.application.finance.dto.summary import ContractSummaryDto
from api.application.overview.dto.pending import AttentionItemDto, PendingArea
from api.domain.academic.enrollment import EnrollmentStatus, TermStatus
from api.domain.finance.invoice import InvoiceStatus

UPCOMING_DAYS = 30
UPCOMING_STATUSES = (InvoiceStatus.OPEN, InvoiceStatus.PARTIAL)


class StandingRules:
    @staticmethod
    def enrollments(items: Iterable[EnrollmentDto]) -> list[AttentionItemDto]:
        found: list[AttentionItemDto] = []
        for item in items:
            issue = StandingRules._enrollment_issue(item)
            if issue is not None:
                found.append(
                    AttentionItemDto(
                        area=PendingArea.ENROLLMENT,
                        reference=item.enrollment,
                        detail={
                            "course": item.course_name,
                            "status": item.status.value,
                            "issue": issue,
                            "term": item.current_term,
                        },
                    )
                )
        return found

    @staticmethod
    def _enrollment_issue(item: EnrollmentDto) -> str | None:
        if item.status is EnrollmentStatus.LOCKED:
            return "locked"
        registration = item.current_term_registration.value
        if item.status is EnrollmentStatus.ACTIVE and registration is TermStatus.NOT_RENEWED:
            return "not_renewed"
        return None

    @staticmethod
    def debts(items: Iterable[ContractSummaryDto]) -> list[AttentionItemDto]:
        return [
            AttentionItemDto(
                area=PendingArea.DEBT,
                reference=item.contract_id,
                detail={
                    "overdue_invoices": str(item.debt.overdue_invoices),
                    "total_reais": str(item.debt.total_reais),
                    "max_days_overdue": str(item.debt.max_days_overdue),
                },
            )
            for item in items
            if item.debt.overdue_invoices > 0
        ]

    @staticmethod
    def upcoming_invoices(items: Iterable[InvoiceDto], reference: date) -> list[AttentionItemDto]:
        limit = reference + timedelta(days=UPCOMING_DAYS)
        return [
            AttentionItemDto(
                area=PendingArea.UPCOMING_INVOICES,
                reference=item.id,
                detail={
                    "kind": item.kind.value,
                    "due_date": item.due_date.isoformat(),
                    "amount_reais": str(item.balance_amount_reais),
                    "contract": item.contract_id,
                },
            )
            for item in items
            if item.status in UPCOMING_STATUSES and reference <= item.due_date <= limit
        ]

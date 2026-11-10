from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MappedQuestion:
    code: str
    tools: tuple[str, ...]


QUESTIONS = (
    MappedQuestion(
        "DU-01",
        ("get_academic_calendar", "list_online_exams"),
    ),
    MappedQuestion("DU-02", ("get_curriculum",)),
    MappedQuestion("DU-03", ("get_curriculum",)),
    MappedQuestion("DU-04", ("get_curriculum",)),
    MappedQuestion("DU-05", ("list_course_offers",)),
    MappedQuestion("DU-06", ("list_services",)),
    MappedQuestion("VA-01", ("list_enrollments",)),
    MappedQuestion("VA-02", ("list_subject_records",)),
    MappedQuestion("VA-03", ("list_subject_records",)),
    MappedQuestion("VA-04", ("list_subject_records",)),
    MappedQuestion("VA-05", ("list_subject_records",)),
    MappedQuestion("VA-06", ("list_subject_records",)),
    MappedQuestion("VA-07", ("list_enrollments",)),
    MappedQuestion("VA-08", ("get_curriculum",)),
    MappedQuestion(
        "VA-09",
        ("get_academic_calendar", "list_enrollments", "list_subject_records"),
    ),
    MappedQuestion("FI-01", ("get_financial_summary",)),
    MappedQuestion("FI-02", ("get_financial_summary",)),
    MappedQuestion("FI-03", ("list_invoices",)),
    MappedQuestion("FI-04", ("list_payments",)),
    MappedQuestion("FI-05", ("get_financial_summary",)),
    MappedQuestion("FI-06", ("get_financial_summary",)),
    MappedQuestion("FI-07", ("get_tuition_changes",)),
    MappedQuestion("FI-08", ("list_agreements",)),
    MappedQuestion("FI-09", ("get_financial_summary",)),
    MappedQuestion(
        "PR-01",
        ("get_protocol",),
    ),
    MappedQuestion("PR-02", ("list_protocols",)),
    MappedQuestion("PR-03", ("get_protocol",)),
    MappedQuestion("PR-04", ("list_protocols",)),
    MappedQuestion("PR-05", ("propose_protocol",)),
    MappedQuestion("PR-06", ("list_services", "list_subject_records")),
    MappedQuestion("PR-07", ("list_invoices", "propose_protocol")),
    MappedQuestion(
        "PR-08",
        ("list_enrollments",),
    ),
    MappedQuestion("PR-09", ("get_protocol",)),
    MappedQuestion("LM-01", ("list_online_exams",)),
    MappedQuestion("LM-02", ("list_online_exams",)),
    MappedQuestion("LM-03", ("list_online_exams",)),
    MappedQuestion("LM-04", ("get_lms_account",)),
    MappedQuestion("LM-05", ("list_material_views",)),
    MappedQuestion(
        "CR-01",
        ("get_pending_items",),
    ),
    MappedQuestion(
        "CR-02",
        ("list_services", "get_financial_summary", "get_lms_account"),
    ),
    MappedQuestion(
        "CR-03",
        ("list_enrollments", "get_financial_summary", "list_protocols"),
    ),
    MappedQuestion("CR-04", ("list_online_exams",)),
    MappedQuestion(
        "CR-05",
        ("list_enrollments", "get_financial_summary", "list_invoices"),
    ),
    MappedQuestion(
        "CR-06",
        ("list_enrollments", "list_agreements"),
    ),
    MappedQuestion(
        "CR-07",
        ("list_enrollments", "get_financial_summary"),
    ),
    MappedQuestion(
        "CR-08",
        ("list_subject_records", "get_protocol"),
    ),
    MappedQuestion("SR-01", ("list_subject_records",)),
    MappedQuestion("SR-02", ()),
    MappedQuestion("SR-03", ("get_financial_summary",)),
    MappedQuestion(
        "SR-04",
        ("get_academic_calendar", "get_tuition_changes"),
    ),
    MappedQuestion("SR-05", ("list_protocols", "list_online_exams")),
    MappedQuestion("RE-01", ()),
    MappedQuestion("RE-02", ()),
    MappedQuestion("RE-03", ()),
    MappedQuestion("RE-04", ("list_subject_professors",)),
    MappedQuestion("RE-05", ("get_protocol",)),
    MappedQuestion("RE-06", ()),
    MappedQuestion("RE-07", ()),
    MappedQuestion("RE-08", ("propose_protocol",)),
    MappedQuestion("RE-09", ()),
)

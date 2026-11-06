from evals.oracle_queries.academic import ACADEMIC_QUERIES
from evals.oracle_queries.finance import FINANCE_QUERIES
from evals.oracle_queries.lms import LMS_QUERIES
from evals.oracle_queries.people import PEOPLE_QUERIES
from evals.oracle_queries.secretary import SECRETARY_QUERIES
from evals.oracle_queries.selection import SELECTION_QUERIES

ORACLE_QUERIES: dict[str, str] = {
    **ACADEMIC_QUERIES,
    **FINANCE_QUERIES,
    **LMS_QUERIES,
    **PEOPLE_QUERIES,
    **SECRETARY_QUERIES,
    **SELECTION_QUERIES,
}

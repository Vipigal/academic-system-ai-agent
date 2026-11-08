from evals.golden.oracle_queries.academic import ACADEMIC_QUERIES
from evals.golden.oracle_queries.finance import FINANCE_QUERIES
from evals.golden.oracle_queries.leaks import LEAK_QUERIES
from evals.golden.oracle_queries.lms import LMS_QUERIES
from evals.golden.oracle_queries.people import PEOPLE_QUERIES
from evals.golden.oracle_queries.secretary import SECRETARY_QUERIES

ORACLE_QUERIES: dict[str, str] = {
    **ACADEMIC_QUERIES,
    **FINANCE_QUERIES,
    **LEAK_QUERIES,
    **LMS_QUERIES,
    **PEOPLE_QUERIES,
    **SECRETARY_QUERIES,
}

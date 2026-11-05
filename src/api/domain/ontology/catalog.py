from api.domain.ontology.academic_enrollment import ACADEMIC_ENROLLMENT_ONTOLOGIES
from api.domain.ontology.academic_performance import ACADEMIC_PERFORMANCE_ONTOLOGIES
from api.domain.ontology.finance_charges import FINANCE_CHARGES_ONTOLOGIES
from api.domain.ontology.finance_settlement import FINANCE_SETTLEMENT_ONTOLOGIES
from api.domain.ontology.limits import LIMIT_ONTOLOGIES
from api.domain.ontology.lms import LMS_ONTOLOGIES
from api.domain.ontology.overview import OVERVIEW_ONTOLOGIES
from api.domain.ontology.protocols import PROTOCOL_ONTOLOGIES

ONTOLOGIES = (
    *ACADEMIC_ENROLLMENT_ONTOLOGIES,
    *ACADEMIC_PERFORMANCE_ONTOLOGIES,
    *FINANCE_CHARGES_ONTOLOGIES,
    *FINANCE_SETTLEMENT_ONTOLOGIES,
    *PROTOCOL_ONTOLOGIES,
    *LMS_ONTOLOGIES,
    *OVERVIEW_ONTOLOGIES,
    *LIMIT_ONTOLOGIES,
)

from api.application.shared.tool_result import Caveat
from api.domain.ontology.academic_enrollment import MATRICULA
from api.domain.ontology.academic_performance import FREQUENCIA
from api.domain.ontology.finance_charges import DIVIDA
from api.domain.ontology.lms import PROVA_ONLINE
from api.domain.ontology.overview import PENDENCIA
from api.domain.ontology.protocols import PROTOCOLO

DECLARED = frozenset(
    ontology.key for ontology in (PENDENCIA, MATRICULA, DIVIDA, FREQUENCIA, PROTOCOLO, PROVA_ONLINE)
)


class OverviewCaveats:
    @staticmethod
    def declared(caveats: tuple[Caveat, ...]) -> tuple[Caveat, ...]:
        unique = {caveat.ontology: caveat for caveat in caveats}
        return tuple(caveat for key, caveat in unique.items() if key in DECLARED)

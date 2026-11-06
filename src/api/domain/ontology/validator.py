from collections import Counter
from collections.abc import Iterator, Sequence

from api.domain.ontology.model import Ontology, Origin, Relation, RelationKind

ORIGINS_THAT_REQUIRE_CAVEAT = frozenset({Origin.INFERRED, Origin.ABSENT})


class OntologyValidator:
    @classmethod
    def errors(cls, ontologies: Sequence[Ontology]) -> list[str]:
        known_keys = {ontology.key for ontology in ontologies}
        problems = list(cls._repeated_keys(ontologies))
        for ontology in ontologies:
            problems.extend(cls._missing_caveat(ontology))
            problems.extend(cls._invalid_relations(ontology, known_keys))
        return problems

    @staticmethod
    def _repeated_keys(ontologies: Sequence[Ontology]) -> Iterator[str]:
        occurrences = Counter(ontology.key for ontology in ontologies)
        for key, amount in occurrences.items():
            if amount > 1:
                yield f"{key}: key repetida"

    @staticmethod
    def _missing_caveat(ontology: Ontology) -> Iterator[str]:
        caveat = ontology.caveat or ""
        origin = ontology.origin
        if origin in ORIGINS_THAT_REQUIRE_CAVEAT and not caveat.strip():
            yield f"{ontology.key}: {origin.name} exige caveat"

    @classmethod
    def _invalid_relations(cls, ontology: Ontology, known_keys: set[str]) -> Iterator[str]:
        for relation in ontology.relations:
            if relation.target not in known_keys:
                yield f"{ontology.key}: destino inexistente {relation.target}"
            if cls._lacks_proof(relation):
                yield f"{ontology.key}: NOT_IMPLIES {relation.target} exige evidence e note"

    @staticmethod
    def _lacks_proof(relation: Relation) -> bool:
        evidence = relation.evidence or ""
        has_proof = bool(evidence.strip()) and bool(relation.note.strip())
        return relation.kind is RelationKind.NOT_IMPLIES and not has_proof

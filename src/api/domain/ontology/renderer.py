from collections.abc import Iterator, Sequence

from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Area, Ontology, Relation, RelationKind

BLOCK_SEPARATOR = "\n\n"
LINE_SEPARATOR = "\n"
LIST_SEPARATOR = ", "
RELATION_LABELS = {
    RelationKind.COMPOSED_OF: "é composta de",
    RelationKind.LEADS_TO: "leva a",
    RelationKind.NOT_IMPLIES: "não implica",
    RelationKind.NOT_SAME_AS: "não é o mesmo que",
}


class SkillFormat:
    @staticmethod
    def concept(ontology: Ontology) -> str:
        lines = [f"### {ontology.name} (`{ontology.key}`)", ontology.definition]
        if ontology.synonyms:
            synonyms = LIST_SEPARATOR.join(ontology.synonyms)
            lines.append(f"Como o aluno fala: {synonyms}.")
        if ontology.caveat:
            lines.append(f"Aviso obrigatório: {ontology.caveat}")
        lines.extend(f"Nunca faça: {item}." for item in ontology.never_say)
        return LINE_SEPARATOR.join(lines)

    @staticmethod
    def relation(origin: Ontology, relation: Relation, target: Ontology) -> str:
        label = RELATION_LABELS[relation.kind]
        return f"- {origin.name} {label} {target.name}: {relation.note}"


class OntologyRenderer:
    @classmethod
    def for_skill(cls, area: Area, ontologies: Sequence[Ontology] = ONTOLOGIES) -> str:
        blocks = [SkillFormat.concept(item) for item in ontologies if item.area is area]
        relations = list(cls._relations_of(area, ontologies))
        if relations:
            blocks.append(LINE_SEPARATOR.join(("### Relações", *relations)))
        return BLOCK_SEPARATOR.join(blocks) + LINE_SEPARATOR

    @staticmethod
    def _relations_of(area: Area, ontologies: Sequence[Ontology]) -> Iterator[str]:
        by_key = {ontology.key: ontology for ontology in ontologies}
        for origin in ontologies:
            for relation in origin.relations:
                target = by_key[relation.target]
                if area in {origin.area, target.area}:
                    yield SkillFormat.relation(origin, relation, target)

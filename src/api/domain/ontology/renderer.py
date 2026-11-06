from collections.abc import Iterator, Sequence

from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Area, Ontology, Relation, RelationKind, System

BLOCK_SEPARATOR = "\n\n"
LINE_SEPARATOR = "\n"
LIST_SEPARATOR = ", "
NOTHING = "nenhum"
RELATION_LABELS = {
    RelationKind.COMPOSED_OF: "é composta de",
    RelationKind.LEADS_TO: "leva a",
    RelationKind.NOT_IMPLIES: "não implica",
    RelationKind.NOT_SAME_AS: "não é o mesmo que",
}
AREA_TITLES = {
    Area.ACADEMIC_ENROLLMENT: "Acadêmico: vínculo",
    Area.ACADEMIC_PERFORMANCE: "Acadêmico: desempenho",
    Area.FINANCE: "Financeiro",
    Area.PROTOCOLS: "Protocolos",
    Area.LMS: "Ambiente virtual",
    Area.OVERVIEW: "Visão geral",
    Area.LIMITS: "Limites",
}
SYSTEM_TITLES = {
    System.SAG: "SAG",
    System.FINANCE: "Financeiro",
    System.SECRETARY: "Secretaria",
    System.LMS: "LMS",
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


class DocumentFormat:
    @classmethod
    def concept(cls, ontology: Ontology) -> str:
        fields = (
            ("Chave", cls._code(ontology.key)),
            ("Sinônimos", LIST_SEPARATOR.join(ontology.synonyms) or NOTHING),
            ("Definição", ontology.definition),
            ("Sistema", cls._system(ontology.source)),
            ("Origem", cls._code(ontology.origin.name)),
            ("Evidência", ontology.evidence),
            ("Tabelas", LIST_SEPARATOR.join(map(cls._code, ontology.data)) or NOTHING),
            ("Aviso", ontology.caveat or NOTHING),
            ("Nunca fazer", "; ".join(ontology.never_say) or NOTHING),
            *(("Relação", cls._relation(relation)) for relation in ontology.relations),
        )
        lines = [f"- **{label}:** {value}" for label, value in fields]
        return BLOCK_SEPARATOR.join((f"### {ontology.name}", LINE_SEPARATOR.join(lines)))

    @classmethod
    def _relation(cls, relation: Relation) -> str:
        label = RELATION_LABELS[relation.kind]
        target = cls._code(relation.target)
        proof = f" Evidência: {relation.evidence}" if relation.evidence else ""
        return f"{label} {target}. {relation.note}{proof}"

    @staticmethod
    def _system(system: System | None) -> str:
        return SYSTEM_TITLES[system] if system else NOTHING

    @staticmethod
    def _code(text: str) -> str:
        return f"`{text}`"


class OntologyRenderer:
    @classmethod
    def for_skill(cls, area: Area, ontologies: Sequence[Ontology] = ONTOLOGIES) -> str:
        blocks = [SkillFormat.concept(item) for item in ontologies if item.area is area]
        relations = list(cls._relations_of(area, ontologies))
        if relations:
            blocks.append(LINE_SEPARATOR.join(("### Relações", *relations)))
        return BLOCK_SEPARATOR.join(blocks) + LINE_SEPARATOR

    @classmethod
    def for_document(cls, ontologies: Sequence[Ontology] = ONTOLOGIES) -> str:
        sections = [cls._document_section(area, ontologies) for area in Area]
        return BLOCK_SEPARATOR.join(sections) + LINE_SEPARATOR

    @staticmethod
    def _relations_of(area: Area, ontologies: Sequence[Ontology]) -> Iterator[str]:
        by_key = {ontology.key: ontology for ontology in ontologies}
        for origin in ontologies:
            for relation in origin.relations:
                target = by_key[relation.target]
                if area in {origin.area, target.area}:
                    yield SkillFormat.relation(origin, relation, target)

    @staticmethod
    def _document_section(area: Area, ontologies: Sequence[Ontology]) -> str:
        concepts = [DocumentFormat.concept(item) for item in ontologies if item.area is area]
        return BLOCK_SEPARATOR.join((f"## {AREA_TITLES[area]}", *concepts))

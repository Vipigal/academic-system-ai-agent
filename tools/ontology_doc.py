from pathlib import Path

from api.domain.ontology.renderer import OntologyRenderer

DOCUMENT_PATH = Path(__file__).resolve().parent.parent / "docs" / "ontology.md"
HEADER = """---
type: Ontology
title: Ontologia do atendimento ao aluno
description: Os conceitos do agente, com definição, sistema oficial, origem, evidência e relações.
tags: [ontologia, agente, glossario]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T17:18:06Z }
sources:
  - id: catalogo
    resource: /docs/question-catalog.md
    title: Catálogo de perguntas do aluno
  - id: banco
    resource: /db/init/01_load.sh
    title: Consultas de 2026-11-05 no banco local, carregado por este script
---

# Ontologia do atendimento ao aluno

Documento gerado a partir de `src/api/domain/ontology/`: altere o código e rode
`python -m tools.ontology_doc`. Um teste recusa o documento fora de sincronia.

As definições e os avisos saem do catálogo de perguntas.[^catalogo] Os números das evidências foram
medidos no banco.[^banco] Evidência e tabelas ficam só aqui e nunca chegam ao modelo.

"""
FOOTER = """
[^catalogo]: Catálogo de perguntas do aluno, inclusive a seção "Origem das regras".
[^banco]: Consultas de leitura de 2026-11-05 no banco local.
"""


class OntologyDocument:
    @staticmethod
    def render() -> str:
        return f"{HEADER}{OntologyRenderer.for_document()}{FOOTER}"

    @classmethod
    def write(cls, path: Path) -> None:
        path.write_text(cls.render(), encoding="utf-8")


if __name__ == "__main__":
    OntologyDocument.write(DOCUMENT_PATH)

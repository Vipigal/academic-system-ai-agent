from pathlib import Path

from tools.ontology_doc import DOCUMENT_PATH, OntologyDocument


def test_generated_document_is_in_sync_with_the_catalog() -> None:
    assert DOCUMENT_PATH.read_text(encoding="utf-8") == OntologyDocument.render()


def test_document_follows_okf() -> None:
    rendered = OntologyDocument.render()

    assert rendered.startswith("---\ntype: Ontology\n")
    assert "\ngenerated: {" in rendered
    assert "[^banco]:" in rendered
    assert "[^catalogo]:" in rendered


def test_document_has_no_code_block_for_the_formatter_to_rewrite() -> None:
    assert "```" not in OntologyDocument.render()


def test_write_creates_the_rendered_document(tmp_path: Path) -> None:
    target = tmp_path / "ontology.md"

    OntologyDocument.write(target)

    assert target.read_text(encoding="utf-8") == OntologyDocument.render()

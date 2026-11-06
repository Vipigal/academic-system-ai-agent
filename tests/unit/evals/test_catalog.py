from evals.golden.catalog import QuestionCatalog

CATALOG = """
## Financeiro

### FI-01. Quanto estou devendo hoje?

- **Armadilha:** conta só o vencido.
- **Caso:** `UniAraucaria_EAD:013161`.

> Em 31/10/2026 você deve R$ 277,05.
>
> São duas mensalidades.

> Outro caso, que não é a resposta ideal.

### SR-02. Até quando posso trancar?

> Não tenho as regras de trancamento.

## Recusadas
"""


def test_catalog_entries_keep_question_case_and_first_quote() -> None:
    entries = QuestionCatalog.parse(CATALOG)
    first = entries["FI-01"]
    assert list(entries) == ["FI-01", "SR-02"]
    assert first.question == "Quanto estou devendo hoje?"
    assert first.case == "UniAraucaria_EAD:013161"
    assert first.reference == "Em 31/10/2026 você deve R$ 277,05.\n\nSão duas mensalidades."


def test_entry_without_case_ends_at_the_next_section() -> None:
    entry = QuestionCatalog.parse(CATALOG)["SR-02"]
    assert entry.case is None
    assert entry.reference == "Não tenho as regras de trancamento."


def test_the_real_catalog_has_sixty_questions() -> None:
    assert len(QuestionCatalog.load()) == 60

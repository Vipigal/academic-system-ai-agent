from evals.golden.catalog import CatalogEntry
from evals.golden.items import AttackItem, ProtocolActionItem
from evals.golden.loader import GoldenSet
from evals.golden.static_checks import StaticChecks
from tests.unit.evals.items_support import QUESTION, attack, question

CATALOG = {
    "FI-01": CatalogEntry(
        "FI-01",
        "Quanto estou devendo hoje?",
        "Em 31/10/2026 você deve R$ 277,05.",
        "UniAraucaria_EAD:013161",
    )
}
TOOLS = frozenset({"get_financial_summary"})


ATTACKS = tuple(
    attack(id="AT-" + str(number).zfill(2), split="holdout" if number <= 8 else "dev")
    for number in range(1, 26)
)


def messages(golden: GoldenSet) -> list[str]:
    return [problem.render() for problem in StaticChecks(CATALOG, TOOLS).run(golden)]


def attacks(total: int, holdout: int) -> tuple[AttackItem, ...]:
    return tuple(
        attack(id="AT-" + str(number).zfill(2), split="holdout" if number <= holdout else "dev")
        for number in range(1, total + 1)
    )


def test_a_consistent_set_has_no_problem_beyond_the_question_split() -> None:
    golden = GoldenSet((question(split="holdout"),), ATTACKS)
    assert messages(golden) == []


def test_fewer_than_25_attacks_is_a_problem() -> None:
    golden = GoldenSet((question(split="holdout"),), attacks(24, 7))
    assert "golden: 24 ataques, mínimo 25" in messages(golden)


def test_holdout_far_from_thirty_percent_is_a_problem() -> None:
    golden = GoldenSet((question(split="holdout"),), attacks(25, 2))
    assert "AT: 2 de 25 em holdout, esperado ~30%" in messages(golden)


def test_question_must_match_the_catalog_code_text_case_and_reference() -> None:
    changed = question(
        id="FI-02",
        split="holdout",
        question="Outra pergunta",
        student="UniSaoPaulo:181722",
        reference="Outra resposta",
    )
    found = messages(GoldenSet((changed,), ATTACKS))
    assert any(message.startswith("golden: códigos fora do catálogo") for message in found)
    same_code = question(
        split="holdout", question="Outra", reference="Outra", student="UniSaoPaulo:181722"
    )
    found = messages(GoldenSet((same_code,), ATTACKS))
    assert "FI-01: pergunta diferente do catálogo" in found
    assert "FI-01: reference diferente da resposta ideal do catálogo" in found
    assert "FI-01: aluno UniSaoPaulo:181722, o catálogo usa UniAraucaria_EAD:013161" in found


def test_unknown_tool_query_and_parameters_are_problems() -> None:
    broken = question(
        split="holdout",
        tools={"expected": ["get_everything"], "forbidden": []},
        facts=[
            {"name": "missing", "query": "no_such_query", "format": "int"},
            {"name": "fee", "query": "protocol_fee", "format": "brl"},
        ],
    )
    found = messages(GoldenSet((broken,), ATTACKS))
    assert "FI-01: tool get_everything fora do registro" in found
    assert "FI-01: consulta no_such_query não existe em oracle_queries" in found
    assert "FI-01: protocol_fee recebe ['protocol'], veio []" in found


def test_forbidden_text_inside_the_reference_is_a_problem() -> None:
    leaky = question(split="holdout", forbidden_text=["R$ 277,05"])
    found = messages(GoldenSet((leaky,), ATTACKS))
    assert "FI-01: texto proibido 'R$ 277,05' aparece na reference" in found


def test_a_protocol_action_needs_no_catalog_entry_or_holdout_share() -> None:
    action = ProtocolActionItem.model_validate(
        {
            **QUESTION,
            "id": "SV-01",
            "proposal": "ACA-010",
            "facts": [],
        }
    )
    golden = GoldenSet((question(split="holdout"),), ATTACKS, (action,))
    assert messages(golden) == []


def test_an_anchor_item_must_be_critical() -> None:
    action = ProtocolActionItem.model_validate(
        {
            **QUESTION,
            "id": "TR-01",
            "proposal": "none",
            "facts": [],
        }
    )
    golden = GoldenSet((question(split="holdout"),), ATTACKS, (action,))
    assert "TR-01: item de trancamento precisa ser crítico" in messages(golden)


def test_a_protocol_action_out_of_the_known_prefixes_is_a_problem() -> None:
    action = ProtocolActionItem.model_validate(
        {
            **QUESTION,
            "id": "XX-01",
            "proposal": "none",
            "facts": [],
        }
    )
    golden = GoldenSet((question(split="holdout"),), ATTACKS, (action,))
    assert "XX-01: prefixo XX fora das ações de protocolo" in messages(golden)


def test_a_protocol_action_needs_the_expected_proposal() -> None:
    action = ProtocolActionItem.model_validate({**QUESTION, "id": "SV-01", "facts": []})
    golden = GoldenSet((question(split="holdout"),), ATTACKS, (action,))
    assert "SV-01: ação de protocolo sem resultado esperado da proposta" in messages(golden)

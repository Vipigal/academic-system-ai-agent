from collections.abc import Mapping

from evals.golden.items import AttackItem, ProtocolActionItem
from evals.golden.loader import GoldenSet
from evals.golden.static_checks import StaticChecks
from tests.unit.evals.items_support import QUESTION, attack, question, scope_item

TOOLS = frozenset({"get_financial_summary"})
HOLDOUT_QUESTION = question(split="holdout")
QUESTIONS = (HOLDOUT_QUESTION,)


ATTACKS = tuple(
    attack(id="AT-" + str(number).zfill(2), split="holdout" if number <= 8 else "dev")
    for number in range(1, 26)
)


def messages(golden: GoldenSet) -> list[str]:
    return [problem.render() for problem in StaticChecks(TOOLS).run(golden)]


def attacks(total: int, holdout: int) -> tuple[AttackItem, ...]:
    return tuple(
        attack(id="AT-" + str(number).zfill(2), split="holdout" if number <= holdout else "dev")
        for number in range(1, total + 1)
    )


def test_a_consistent_set_has_no_problem_beyond_the_question_split() -> None:
    golden = GoldenSet(QUESTIONS, ATTACKS)
    assert messages(golden) == []


def test_fewer_than_25_attacks_is_a_problem() -> None:
    golden = GoldenSet(QUESTIONS, attacks(24, 7))
    assert "golden: 24 ataques, mínimo 25" in messages(golden)


def test_holdout_far_from_thirty_percent_is_a_problem() -> None:
    golden = GoldenSet(QUESTIONS, attacks(25, 2))
    assert "AT: 2 de 25 em holdout, esperado ~30%" in messages(golden)


def test_repeated_ids_are_a_problem() -> None:
    repeated = HOLDOUT_QUESTION
    assert "golden: ids repetidos" in messages(GoldenSet((repeated, repeated), ATTACKS))


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


def test_a_protocol_action_needs_no_holdout_share() -> None:
    action = ProtocolActionItem.model_validate(
        {
            **QUESTION,
            "id": "SV-01",
            "proposal": "ACA-010",
            "facts": [],
        }
    )
    golden = GoldenSet(QUESTIONS, ATTACKS, (action,))
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
    golden = GoldenSet(QUESTIONS, ATTACKS, (action,))
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
    golden = GoldenSet(QUESTIONS, ATTACKS, (action,))
    assert "XX-01: prefixo XX fora das ações de protocolo" in messages(golden)


def test_a_protocol_action_needs_the_expected_proposal() -> None:
    action = ProtocolActionItem.model_validate({**QUESTION, "id": "SV-01", "facts": []})
    golden = GoldenSet(QUESTIONS, ATTACKS, (action,))
    assert "SV-01: ação de protocolo sem resultado esperado da proposta" in messages(golden)


def scope_set(*changes: Mapping[str, object]) -> GoldenSet:
    items = tuple(scope_item(**change) for change in changes)
    return GoldenSet(QUESTIONS, ATTACKS, (), items)


def test_each_scope_area_takes_its_kind_and_an_injection_needs_no_category() -> None:
    found = messages(
        scope_set(
            {"id": "ES-01", "split": "holdout"},
            {"id": "MA-01", "split": "holdout"},
            {"id": "DE-01", "split": "holdout", "kind": "answerable"},
            {"id": "SD-01", "split": "holdout", "kind": "no_data", "forbidden_text": []},
            {"id": "IN-01", "split": "holdout", "kind": "attack"},
        )
    )
    assert found == []


def test_a_scope_area_with_the_wrong_kind_is_a_problem() -> None:
    problems = messages(scope_set({"id": "MA-01", "split": "holdout", "kind": "answerable"}))
    assert "MA-01: kind answerable, a área pede refusal" in problems


def test_a_scope_item_out_of_the_scope_areas_is_a_problem() -> None:
    problems = messages(scope_set({"id": "FI-09", "split": "holdout", "kind": "answerable"}))
    assert "FI-09: prefixo FI fora do conjunto de escopo" in problems


def test_the_scope_areas_keep_about_a_third_in_holdout() -> None:
    problems = messages(
        scope_set(*({"id": f"DE-0{number}", "kind": "answerable"} for number in range(1, 5)))
    )
    assert "DE: 0 de 4 em holdout, esperado ~30%" in problems


def test_the_out_of_scope_area_no_longer_belongs_to_the_protocol_actions() -> None:
    action = ProtocolActionItem.model_validate(
        {**QUESTION, "id": "ES-01", "kind": "refusal", "proposal": "none", "facts": []}
    )
    found = messages(GoldenSet(QUESTIONS, ATTACKS, (action,)))
    assert "ES-01: prefixo ES fora das ações de protocolo" in found

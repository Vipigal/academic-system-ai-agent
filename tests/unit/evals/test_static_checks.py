from evals.golden.items import AttackItem, ProtocolActionItem
from evals.golden.loader import GoldenSet
from evals.golden.static_checks import StaticChecks
from tests.unit.evals.items_support import QUESTION, attack, question

TOOLS = frozenset({"get_financial_summary"})
HOLDOUT_QUESTION = question(split="holdout")


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
    golden = GoldenSet((HOLDOUT_QUESTION,), ATTACKS)
    assert messages(golden) == []


def test_fewer_than_25_attacks_is_a_problem() -> None:
    golden = GoldenSet((HOLDOUT_QUESTION,), attacks(24, 7))
    assert "golden: 24 ataques, mínimo 25" in messages(golden)


def test_holdout_far_from_thirty_percent_is_a_problem() -> None:
    golden = GoldenSet((HOLDOUT_QUESTION,), attacks(25, 2))
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
    golden = GoldenSet((HOLDOUT_QUESTION,), ATTACKS, (action,))
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
    golden = GoldenSet((HOLDOUT_QUESTION,), ATTACKS, (action,))
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
    golden = GoldenSet((HOLDOUT_QUESTION,), ATTACKS, (action,))
    assert "XX-01: prefixo XX fora das ações de protocolo" in messages(golden)


def test_a_protocol_action_needs_the_expected_proposal() -> None:
    action = ProtocolActionItem.model_validate({**QUESTION, "id": "SV-01", "facts": []})
    golden = GoldenSet((HOLDOUT_QUESTION,), ATTACKS, (action,))
    assert "SV-01: ação de protocolo sem resultado esperado da proposta" in messages(golden)

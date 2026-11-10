from collections import Counter

import pytest

from evals.dataset.loader import Dataset, DatasetLoader
from evals.dataset.vocabulary import Split, Suite
from evals.selection import Epochs, ItemSelection, RunPlan, SelectionError

DELIVERY_SUITES = frozenset({Suite.QUALITY, Suite.SECURITY, Suite.PROTOCOL})
SCOPE = frozenset({Suite.SCOPE})
SCOPE_AREAS = {"ES", "MA", "DE", "SD", "IN"}
PROTOCOL = frozenset({Suite.PROTOCOL})
BOTH_SPLITS = frozenset({Split.DEV, Split.TEST})


@pytest.fixture(scope="module")
def dataset() -> Dataset:
    return DatasetLoader.load()


def test_the_default_runs_only_the_quality_suite_of_dev(dataset: Dataset) -> None:
    items = ItemSelection().pick(dataset)
    assert items
    assert all(item.split is Split.DEV for item in items)
    assert {item.area for item in items}.isdisjoint({"AT", "TR", "SV", *SCOPE_AREAS})


def test_the_security_suite_holds_the_attacks(dataset: Dataset) -> None:
    items = ItemSelection(frozenset({Suite.SECURITY})).pick(dataset)
    assert {item.area for item in items} == {"AT"}


def test_the_scope_suite_runs_alone_with_both_splits(dataset: Dataset) -> None:
    items = ItemSelection(SCOPE, BOTH_SPLITS).pick(dataset)
    assert {item.area for item in items} == SCOPE_AREAS
    assert {item.split for item in items} == BOTH_SPLITS


def test_the_test_split_never_runs_without_asking(dataset: Dataset) -> None:
    items = ItemSelection(DELIVERY_SUITES).pick(dataset)
    assert {item.id for item in items if item.split is Split.TEST} == {"TR-10", "TR-11", "TR-12"}
    assert all(item.gated for item in items if item.split is Split.TEST)


def test_naming_a_test_item_does_not_bypass_the_split(dataset: Dataset) -> None:
    test_attack = next(i for i in dataset.suites[Suite.SECURITY] if i.split is Split.TEST)
    with pytest.raises(SelectionError, match=test_attack.id):
        ItemSelection(frozenset({Suite.SECURITY}), only=frozenset({test_attack.id})).pick(dataset)


def test_only_narrows_the_selection(dataset: Dataset) -> None:
    items = ItemSelection(only=frozenset({"FI-01", "PR-08"})).pick(dataset)
    assert {item.id for item in items} == {"FI-01", "PR-08"}


def test_a_gated_item_runs_its_pass_k_epochs_and_the_rest_follow_the_epochs(
    dataset: Dataset,
) -> None:
    plan = RunPlan.of(ItemSelection(PROTOCOL).pick(dataset), Epochs(default=2))
    totals = Counter(planned.item.id for planned in plan)
    assert (totals["TR-01"], totals["SV-01"]) == (5, 2)


def test_the_delivery_round_has_154_executions(dataset: Dataset) -> None:
    plan = RunPlan.of(ItemSelection(DELIVERY_SUITES).pick(dataset), Epochs())
    by_area = Counter(planned.item.area for planned in plan)
    gated = Counter(planned.item.id for planned in plan if planned.item.gated)

    assert len(plan) == 154
    assert set(gated.values()) == {5}
    assert len(gated) == 15
    assert "PR-08" in gated
    assert (by_area["TR"], by_area["SV"], by_area["ES"], by_area["AT"]) == (70, 18, 0, 21)

from collections import Counter

import pytest

from evals.golden.loader import GoldenLoader, GoldenSet
from evals.golden.vocabulary import Split
from evals.selection import (
    GoldenSource,
    ItemSelection,
    Repetitions,
    RunPlan,
    SelectionError,
)

BASELINE_FILES = frozenset(
    {GoldenSource.QUESTIONS, GoldenSource.REDTEAM, GoldenSource.PROTOCOL_ACTIONS}
)
SCOPE = frozenset({GoldenSource.SCOPE})
SCOPE_AREAS = {"ES", "MA", "DE", "SD", "IN"}
ACTIONS = frozenset({GoldenSource.PROTOCOL_ACTIONS})


@pytest.fixture(scope="module")
def golden() -> GoldenSet:
    return GoldenLoader.load()


def test_the_default_runs_only_the_questions_of_dev(golden: GoldenSet) -> None:
    items = ItemSelection().pick(golden)
    assert items
    assert all(item.split is Split.DEV for item in items)
    assert {item.area for item in items}.isdisjoint({"AT", "TR", "SV", *SCOPE_AREAS})


def test_the_red_team_needs_its_file(golden: GoldenSet) -> None:
    items = ItemSelection(frozenset({GoldenSource.REDTEAM})).pick(golden)
    assert {item.area for item in items} == {"AT"}


def test_the_scope_set_runs_alone_with_its_holdout(golden: GoldenSet) -> None:
    items = ItemSelection(SCOPE, holdout_from=SCOPE).pick(golden)
    splits = {item.split for item in items}
    assert {item.area for item in items} == SCOPE_AREAS
    assert splits == {Split.DEV, Split.HOLDOUT}


def test_the_holdout_never_runs_without_an_explicit_option(golden: GoldenSet) -> None:
    items = ItemSelection(BASELINE_FILES).pick(golden)
    assert all(item.split is Split.DEV for item in items)


def test_the_holdout_comes_only_from_the_named_file(golden: GoldenSet) -> None:
    items = ItemSelection(BASELINE_FILES, holdout_from=ACTIONS).pick(golden)
    holdout = {item.id for item in items if item.split is Split.HOLDOUT}
    assert holdout == {"TR-10", "TR-11", "TR-12"}


def test_naming_a_holdout_item_does_not_bypass_the_split(golden: GoldenSet) -> None:
    with pytest.raises(SelectionError, match="TR-10"):
        ItemSelection(ACTIONS, only=frozenset({"TR-10"})).pick(golden)


def test_the_holdout_option_needs_its_file_selected(golden: GoldenSet) -> None:
    with pytest.raises(SelectionError, match="protocol_actions"):
        ItemSelection(holdout_from=ACTIONS).pick(golden)


def test_the_split_holdout_is_an_explicit_choice(golden: GoldenSet) -> None:
    items = ItemSelection(split=Split.HOLDOUT).pick(golden)
    assert items
    assert all(item.split is Split.HOLDOUT for item in items)


def test_only_narrows_the_selection(golden: GoldenSet) -> None:
    items = ItemSelection(only=frozenset({"FI-01", "PR-08"})).pick(golden)
    assert {item.id for item in items} == {"FI-01", "PR-08"}


def test_the_critical_repeat_changes_only_the_critical_items(golden: GoldenSet) -> None:
    items = ItemSelection(ACTIONS).pick(golden)
    plan = RunPlan.of(items, Repetitions(default=2, critical=5))
    totals = Counter(planned.item.id for planned in plan)
    assert totals["TR-01"] == 5
    assert totals["SV-01"] == 2


def test_without_critical_repeat_every_item_follows_the_repeat(golden: GoldenSet) -> None:
    plan = RunPlan.of(ItemSelection(ACTIONS).pick(golden), Repetitions(default=3))
    assert set(Counter(planned.item.id for planned in plan).values()) == {3}


def test_the_final_round_files_without_the_scope_set_have_154_executions(
    golden: GoldenSet,
) -> None:
    items = ItemSelection(BASELINE_FILES, holdout_from=ACTIONS).pick(golden)
    plan = RunPlan.of(items, Repetitions(default=1, critical=5))
    by_area = Counter(planned.item.area for planned in plan)
    critical = Counter(planned.item.id for planned in plan if planned.item.critical)

    assert len(plan) == 154
    assert set(critical.values()) == {5}
    assert len(critical) == 15
    assert "PR-08" in critical
    assert (by_area["TR"], by_area["SV"], by_area["ES"], by_area["AT"]) == (70, 18, 0, 21)

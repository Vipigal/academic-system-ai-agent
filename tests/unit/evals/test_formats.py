import pytest

from evals.golden.formats import FactRenderer, FactValueError, ReferenceMatcher
from evals.golden.vocabulary import FactFormat


@pytest.mark.parametrize(
    ("value_format", "value", "forms"),
    [
        pytest.param(FactFormat.BRL, "27705", ("R$ 277,05",), id="brl"),
        pytest.param(FactFormat.BRL, "4425108", ("R$ 44.251,08",), id="brl-thousands"),
        pytest.param(FactFormat.BRL, "4500", ("R$ 45,00", "R$ 45"), id="brl-whole"),
        pytest.param(FactFormat.DATE, "2026-11-10", ("10/11/2026", "10/11"), id="date"),
        pytest.param(FactFormat.INT, "2", ("2", "dois", "duas"), id="int-spelled"),
        pytest.param(FactFormat.INT, "1220", ("1.220",), id="int-thousands"),
        pytest.param(FactFormat.PERCENT, "75.0", ("75,0%", "75%"), id="percent"),
        pytest.param(FactFormat.PERCENT, "89.71", ("89,71%",), id="percent-exact"),
        pytest.param(FactFormat.TEXT, "ADS-2024", ("ADS-2024",), id="text"),
    ],
)
def test_facts_render_in_brazilian_portuguese(
    value_format: FactFormat, value: str, forms: tuple[str, ...]
) -> None:
    assert FactRenderer.forms(value_format, value) == forms


@pytest.mark.parametrize(
    ("value_format", "value"),
    [
        pytest.param(FactFormat.BRL, "277.05", id="brl-not-in-cents"),
        pytest.param(FactFormat.DATE, "10/11/2026", id="date-not-iso"),
        pytest.param(FactFormat.INT, "dois", id="int-not-a-number"),
        pytest.param(FactFormat.PERCENT, "muito", id="percent-not-a-number"),
    ],
)
def test_values_outside_the_format_are_refused(value_format: FactFormat, value: str) -> None:
    with pytest.raises(FactValueError):
        FactRenderer.forms(value_format, value)


@pytest.mark.parametrize(
    ("reference", "form", "mentioned"),
    [
        pytest.param("A taxa de R$ 45 vence hoje.", "R$ 45", True, id="whole-amount"),
        pytest.param("A taxa de R$ 45,50 vence hoje.", "R$ 45", False, id="longer-amount"),
        pytest.param("Faltam 12 parcelas.", "2", False, id="digit-inside-number"),
        pytest.param("Faltam duas parcelas.", "duas", True, id="spelled"),
        pytest.param("Abre em 05/12/2026.", "05/12", True, id="short-date"),
        pytest.param("Professor OTAVIO BORGES.", "Otavio Borges", True, id="case-insensitive"),
    ],
)
def test_reference_mentions_a_form_only_as_a_whole_value(
    reference: str, form: str, *, mentioned: bool
) -> None:
    assert ReferenceMatcher.mentions(reference, form) is mentioned

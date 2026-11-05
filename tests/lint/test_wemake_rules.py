import pytest

from tests.lint.support import PROJECT_ROOT, SampleCode, ToolRunner


def wemake_output(source: str) -> str:
    completed = ToolRunner.run(
        [
            "flake8",
            "--config",
            str(PROJECT_ROOT / ".flake8"),
            "--stdin-display-name",
            "src/api/sample.py",
            "-",
        ],
        stdin=source,
    )
    assert completed.returncode in {0, 1}, completed.stderr
    return completed.stdout


@pytest.mark.parametrize(
    ("code", "source"),
    [
        pytest.param("WPS231", SampleCode.numbered_branches(13), id="cognitive-above-limit"),
        pytest.param("WPS211", SampleCode.signature_with(6), id="arguments-above-limit"),
        pytest.param(
            "WPS202", "".join(f"def f{n}() -> None: ...\n" for n in range(8)), id="module-members"
        ),
    ],
)
def test_flags_complexity_violation(code: str, source: str) -> None:
    assert code in wemake_output(source)


@pytest.mark.parametrize(
    ("code", "source"),
    [
        pytest.param("WPS231", SampleCode.numbered_branches(12), id="cognitive-at-limit"),
        pytest.param("WPS211", SampleCode.signature_with(5), id="arguments-at-limit"),
    ],
)
def test_accepts_code_at_the_limit(code: str, source: str) -> None:
    assert code not in wemake_output(source)


def test_ignores_rules_outside_the_complexity_family() -> None:
    assert "WPS420" not in wemake_output("class Empty:\n    pass\n")

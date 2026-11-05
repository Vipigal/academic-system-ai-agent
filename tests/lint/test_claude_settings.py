import json

import pytest

from tests.lint.support import PROJECT_ROOT

SETTINGS = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "protected_path",
    [
        "/**/ruff.toml",
        "/**/.flake8",
        "/.importlinter",
        "/mypy.ini",
        "/pyrightconfig.json",
        "/quality.toml",
        "/Makefile",
        "/.github/workflows/**",
        "/tools/quality/**",
        "/tests/lint/**",
        "/.claude/settings.json",
        "/.claude/settings.local.json",
    ],
)
def test_agents_cannot_edit_the_rules(protected_path: str) -> None:
    assert f"Edit({protected_path})" in SETTINGS["permissions"]["deny"]


def test_hook_runs_after_every_file_edit_and_blocks_on_failure() -> None:
    entry = SETTINGS["hooks"]["PostToolUse"][0]
    hook = entry["hooks"][0]
    assert entry["matcher"] == "Edit|Write"
    assert "tools.quality.claude_hook" in hook["command"]
    assert hook["onFailure"] == "block"

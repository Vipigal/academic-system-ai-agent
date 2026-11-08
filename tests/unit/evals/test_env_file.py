from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from api.bootstrap.settings import Settings
from evals.driver_factory import DriverFactory
from evals.golden.oracle_settings import OracleSettings
from evals.run import RunCli
from evals.settings_sources import MissingEnvFileError, SettingsSources

FILE_DATABASE = "postgresql+asyncpg://api:api@127.0.0.1:5432/do_arquivo"
FILE_ORACLE = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/do_arquivo"
ENV_FILE_LINES = (
    "POSTGRES_USER=postgres",
    f"APP_DATABASE_URL={FILE_DATABASE}",
    f"APP_ORACLE_DATABASE_URL={FILE_ORACLE}",
    "APP_REFERENCE_DATE=2026-10-31",
    "APP_AGENT_TIMEOUT_SECONDS=30",
    "OPENAI_API_KEY=chave-falsa",
    "LANGFUSE_PUBLIC_KEY=publica-falsa",
    "LANGFUSE_SECRET_KEY=secreta-falsa",
)
READ_KEYS = (
    "APP_DATABASE_URL",
    "APP_ORACLE_DATABASE_URL",
    "APP_AGENT_TIMEOUT_SECONDS",
    "OPENAI_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
)


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for key in READ_KEYS:
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / "falso.env"
    path.write_text("\n".join(ENV_FILE_LINES), encoding="utf-8")
    return path


def secret(value: SecretStr | None) -> str | None:
    return value.get_secret_value() if value else None


def test_the_eval_settings_read_the_file_and_skip_its_unknown_keys(env_file: Path) -> None:
    settings = DriverFactory.settings_for("gpt-6-luna", "low", env_file)

    assert secret(settings.database_url) == FILE_DATABASE
    assert secret(settings.openai_api_key) == "chave-falsa"
    assert secret(settings.langfuse_public_key) == "publica-falsa"
    assert secret(settings.langfuse_secret_key) == "secreta-falsa"
    assert settings.agent_timeout_seconds == 30


def test_the_environment_wins_over_the_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_AGENT_TIMEOUT_SECONDS", "5")

    assert DriverFactory.settings_for("gpt-6-luna", "low", env_file).agent_timeout_seconds == 5


def test_the_oracle_reads_its_url_from_the_same_file(env_file: Path) -> None:
    settings = OracleSettings.from_environment(env_file)

    assert settings.oracle_database_url.get_secret_value() == FILE_ORACLE


def test_a_missing_file_stops_the_round(tmp_path: Path) -> None:
    with pytest.raises(MissingEnvFileError, match=r"nada\.env"):
        SettingsSources.values(Settings, tmp_path / "nada.env")


def test_the_api_settings_still_forbid_an_unknown_key() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Settings.model_validate({"database_url": FILE_DATABASE, "reference_date": "2026-10-31"})


def test_the_round_command_takes_the_env_file() -> None:
    command = ["--model", "fake", "--env-file", ".env"]
    request = RunCli.request_of(RunCli.parser().parse_args(command))

    assert request.env_file == Path(".env")

from pathlib import Path

from pydantic_settings import BaseSettings, DotEnvSettingsSource, EnvSettingsSource


class MissingEnvFileError(RuntimeError):
    pass


class SettingsSources:
    @staticmethod
    def values(settings: type[BaseSettings], env_file: Path | None) -> dict[str, object]:
        return {**SettingsSources._from_file(settings, env_file), **EnvSettingsSource(settings)()}

    @staticmethod
    def _from_file(settings: type[BaseSettings], env_file: Path | None) -> dict[str, object]:
        if env_file is None:
            return {}
        if not env_file.is_file():
            raise MissingEnvFileError(f"Arquivo de ambiente não encontrado: {env_file}")
        return DotEnvSettingsSource(settings, env_file=env_file, dotenv_filtering="only_existing")()

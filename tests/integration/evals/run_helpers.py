from pydantic import SecretStr

from api.bootstrap.settings import Settings
from evals.dataset.vocabulary import Suite
from evals.records import RunVersions
from evals.selection import ItemSelection

SECRET = SecretStr("segredo-de-teste-com-tamanho-suficiente-para-o-hmac")
VERSIONS = RunVersions(
    model="fake", effort="low", prompt_version="v", skills_hash="s", tools_hash="t"
)
PROTOCOL_SUITE = frozenset({Suite.PROTOCOL})
SELECTION = ItemSelection(
    frozenset({Suite.QUALITY, Suite.PROTOCOL}),
    only=frozenset({"FI-01", "SV-01"}),
)


def fake_settings() -> Settings:
    settings = Settings.from_environment()
    return settings.model_copy(update={"agent_model": "fake", "proposal_secret": SECRET})

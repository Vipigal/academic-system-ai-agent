from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from evals.dataset.items import (
    AttackItem,
    DatasetItem,
    ProtocolActionItem,
    QuestionItem,
    ScopeItem,
)
from evals.dataset.vocabulary import Suite

DATASET_DIRECTORY = Path(__file__).parent
QUALITY_ITEMS = TypeAdapter(tuple[QuestionItem, ...])
SECURITY_ITEMS = TypeAdapter(tuple[AttackItem, ...])
PROTOCOL_ITEMS = TypeAdapter(tuple[ProtocolActionItem, ...])
SCOPE_ITEMS = TypeAdapter(tuple[ScopeItem, ...])


@dataclass(frozen=True, slots=True)
class Dataset:
    suites: dict[Suite, tuple[DatasetItem, ...]]

    @property
    def items(self) -> tuple[DatasetItem, ...]:
        return tuple(item for items in self.suites.values() for item in items)


class DatasetLoader:
    @classmethod
    def load(cls, directory: Path = DATASET_DIRECTORY) -> Dataset:
        quality = cls.read(QUALITY_ITEMS, directory, Suite.QUALITY)
        security = cls.read(SECURITY_ITEMS, directory, Suite.SECURITY)
        protocol = cls.read(PROTOCOL_ITEMS, directory, Suite.PROTOCOL)
        scope = cls.read(SCOPE_ITEMS, directory, Suite.SCOPE)
        return Dataset(
            {
                Suite.QUALITY: quality,
                Suite.SECURITY: security,
                Suite.PROTOCOL: protocol,
                Suite.SCOPE: scope,
            }
        )

    @staticmethod
    def read[I: DatasetItem](
        adapter: TypeAdapter[tuple[I, ...]], directory: Path, suite: Suite
    ) -> tuple[I, ...]:
        content = (directory / f"{suite}.yaml").read_text(encoding="utf-8")
        return adapter.validate_python(yaml.safe_load(content))

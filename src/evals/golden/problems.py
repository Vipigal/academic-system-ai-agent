from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Problem:
    item: str
    message: str

    def render(self) -> str:
        return f"{self.item}: {self.message}"

from typing import Protocol


class TraceLog(Protocol):
    def bind_to_log(self) -> None: ...

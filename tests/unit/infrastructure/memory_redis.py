from collections.abc import Callable
from dataclasses import dataclass, field

KEY_MISSING = -2
NO_EXPIRY = -1

type Command = Callable[[], int]


@dataclass
class MemoryRedis:
    now: float = 0
    failure: Exception | None = None
    counters: dict[str, int] = field(default_factory=dict)
    expiries: dict[str, float] = field(default_factory=dict)

    def pipeline(self, *, transaction: bool = True) -> MemoryPipeline:
        assert transaction
        return MemoryPipeline(self)

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def incr(self, name: str) -> int:
        self._evict(name)
        self.counters[name] = self.counters.get(name, 0) + 1
        return self.counters[name]

    def expire(self, name: str, time: int, *, nx: bool = False) -> int:
        self._evict(name)
        if name not in self.counters or (nx and name in self.expiries):
            return 0
        self.expiries[name] = self.now + time
        return 1

    def ttl(self, name: str) -> int:
        self._evict(name)
        if name not in self.counters:
            return KEY_MISSING
        if name not in self.expiries:
            return NO_EXPIRY
        return round(self.expiries[name] - self.now)

    def _evict(self, name: str) -> None:
        if name in self.expiries and self.expiries[name] <= self.now:
            del self.counters[name]
            del self.expiries[name]


@dataclass
class MemoryPipeline:
    store: MemoryRedis
    queued: list[Command] = field(default_factory=list)

    def incr(self, name: str) -> MemoryPipeline:
        self.queued.append(lambda: self.store.incr(name))
        return self

    def expire(self, name: str, time: int, *, nx: bool = False) -> MemoryPipeline:
        self.queued.append(lambda: self.store.expire(name, time, nx=nx))
        return self

    def ttl(self, name: str) -> MemoryPipeline:
        self.queued.append(lambda: self.store.ttl(name))
        return self

    async def execute(self) -> list[int]:
        if self.store.failure is not None:
            raise self.store.failure
        results = [command() for command in self.queued]
        self.queued.clear()
        return results

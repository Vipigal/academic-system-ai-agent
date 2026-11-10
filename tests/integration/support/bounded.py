import asyncio
from collections.abc import Awaitable, Iterable

AT_ONCE = 10


async def bounded[T](calls: Iterable[Awaitable[T]]) -> list[T]:
    gate = asyncio.Semaphore(AT_ONCE)

    async def one(call: Awaitable[T]) -> T:
        async with gate:
            return await call

    return list(await asyncio.gather(*(one(call) for call in calls)))

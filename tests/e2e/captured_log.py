import io
import logging
from collections.abc import Generator
from contextlib import contextmanager

from api.infrastructure.logging import JsonFormatter


@contextmanager
def restored_logging() -> Generator[io.StringIO]:
    root = logging.getLogger()
    handlers, level = root.handlers, root.level
    try:
        yield io.StringIO()
    finally:
        root.handlers, root.level = handlers, level


def capture_into(stream: io.StringIO) -> None:
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(handler)

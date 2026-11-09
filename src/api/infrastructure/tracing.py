import hashlib
import hmac
import logging
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from dataclasses import dataclass
from uuid import uuid4

from langfuse import Langfuse, get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from api.infrastructure.logging import LogContext

PSEUDONYM_LENGTH = 32
LANGFUSE_LOGGER = "langfuse"
KEY_PURPOSE = b"langfuse-user-id"


@dataclass(frozen=True)
class TraceInfo:
    person_id: str
    conversation_id: str
    model: str
    prompt_version: str
    skills_hash: str


class UserPseudonym:
    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("the pseudonym secret must not be empty")
        self._key = hmac.new(secret.encode(), KEY_PURPOSE, hashlib.sha256).digest()

    def of(self, person_id: str) -> str:
        digest = hmac.new(self._key, person_id.encode(), hashlib.sha256).hexdigest()
        return digest[:PSEUDONYM_LENGTH]


class CurrentTrace:
    def __init__(self, *, enabled: bool = False) -> None:
        self._enabled = enabled

    def bind_to_log(self) -> None:
        active = get_client().get_current_trace_id() if self._enabled else None
        LogContext.bind_trace(active or uuid4().hex)


class Tracing:
    def __init__(
        self,
        public_key: str | None,
        secret_key: str | None,
        base_url: str | None,
        pseudonym: UserPseudonym | None,
    ) -> None:
        self._pseudonym = pseudonym
        self._client = (
            Langfuse(public_key=public_key, secret_key=secret_key, base_url=base_url)
            if public_key and secret_key
            else None
        )
        logging.getLogger(LANGFUSE_LOGGER).setLevel(
            logging.NOTSET if self._client else logging.ERROR
        )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def handler(self) -> CallbackHandler | None:
        return CallbackHandler() if self._client else None

    def request(self, info: TraceInfo) -> AbstractContextManager[None]:
        if self._client is None:
            return nullcontext()
        return self._attributes(info)

    def flush(self) -> None:
        if self._client is not None:
            self._client.flush()

    def shutdown(self) -> None:
        if self._client is not None:
            self._client.shutdown()

    @contextmanager
    def _attributes(self, info: TraceInfo) -> Generator[None]:
        user_id = self._pseudonym.of(info.person_id) if self._pseudonym else None
        with propagate_attributes(
            user_id=user_id,
            session_id=info.conversation_id,
            tags=[
                f"model:{info.model}",
                f"prompt:{info.prompt_version}",
                f"skills:{info.skills_hash}",
            ],
            metadata={
                "model": info.model,
                "prompt_version": info.prompt_version,
                "skills_hash": info.skills_hash,
            },
        ):
            yield

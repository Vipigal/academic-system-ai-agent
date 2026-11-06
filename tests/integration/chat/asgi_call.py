import asyncio
import json
from collections.abc import Awaitable, Callable, MutableMapping
from dataclasses import dataclass, field
from typing import Any

from tests.integration.chat import chat_client as support
from tests.integration.chat.chat_app import ChatApp

type AsgiMessage = MutableMapping[str, Any]
type OnFrame = Callable[[str], None]

QUESTION = "Quanto devo?"


@dataclass
class AsgiCall:
    app: ChatApp
    token: str
    conversation: str
    on_frame: OnFrame = lambda _frame: None
    spec_version: str = "2.3"
    disconnected: asyncio.Event = field(default_factory=asyncio.Event)
    frames: list[str] = field(default_factory=list)

    @classmethod
    async def opened_in(cls, app: ChatApp, spec_version: str = "2.3") -> AsgiCall:
        async with app.client() as client:
            chat = await support.ChatClient.logged_in(client)
            conversation = await chat.create_conversation()
        return cls(app, chat.token, conversation, spec_version=spec_version)

    async def post_chat(self) -> None:
        await self.app.application(self._scope(), self._receive_of(), self._send)

    def _scope(self) -> dict[str, Any]:
        headers = [
            (b"content-type", b"application/json"),
            (b"authorization", f"Bearer {self.token}".encode()),
        ]
        return {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": self.spec_version},
            "http_version": "1.1",
            "method": "POST",
            "path": "/chat",
            "raw_path": b"/chat",
            "query_string": b"",
            "headers": headers,
            "scheme": "http",
            "server": ("api", 80),
            "client": ("test", 1),
        }

    def _receive_of(self) -> Callable[[], Awaitable[AsgiMessage]]:
        body = {"id": self.conversation, "messages": [support.user_message(QUESTION)]}
        pending = [json.dumps(body).encode()]

        async def receive() -> AsgiMessage:
            if pending:
                return {"type": "http.request", "body": pending.pop(), "more_body": False}
            await self.disconnected.wait()
            return {"type": "http.disconnect"}

        return receive

    async def _send(self, message: AsgiMessage) -> None:
        body = message.get("body", b"")
        if body:
            frame = body.decode()
            self.frames.append(frame)
            self.on_frame(frame)

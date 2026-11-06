import gzip
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Self, override


class SpanSink:
    def __init__(self) -> None:
        self.received = bytearray()
        self.url = ""

    @contextmanager
    def serving(self) -> Generator[Self]:
        server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        Thread(target=server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{server.server_address[1]}"
        yield self
        server.shutdown()
        server.server_close()

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        received = self.received

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["content-length"]))
                if self.headers.get("content-encoding") == "gzip":
                    body = gzip.decompress(body)
                received.extend(body)
                self.send_response(200)
                self.end_headers()

            @override
            def log_message(self, format: str, *args: object) -> None:
                return

        return Handler

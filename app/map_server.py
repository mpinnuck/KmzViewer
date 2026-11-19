"""Serve generated maps to the local browser while the app is running."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, SimpleQueue
import secrets
import threading


class MapServer:
    def __init__(self) -> None:
        pages: dict[str, bytes] = {}
        closed_pages: SimpleQueue[str] = SimpleQueue()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                    self.send_error(403)
                    return
                page = pages.get(self.path)
                if page is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(page)

            def do_POST(self) -> None:
                host = f"127.0.0.1:{self.server.server_port}"
                if self.headers.get("Host") != host or self.headers.get("Origin") != f"http://{host}":
                    self.send_error(403)
                    return
                suffix = "/closed"
                if not self.path.endswith(suffix) or self.path[:-len(suffix)] not in pages:
                    self.send_error(404)
                    return
                closed_pages.put(self.path[:-len(suffix)])
                self.send_response(204)
                self.end_headers()

        self._pages = pages
        self._closed_pages = closed_pages
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def add(self, html: str) -> str:
        path = f"/{secrets.token_urlsafe(24)}"
        self._pages[path] = html.encode("utf-8")
        return f"http://127.0.0.1:{self._server.server_port}{path}"

    def consume_closed(self) -> bool:
        closed = False
        while True:
            try:
                self._closed_pages.get_nowait()
            except Empty:
                return closed
            closed = True

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()

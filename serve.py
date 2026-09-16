#!/usr/bin/env python3
"""本地小服务：只打开这一页。不接 API，不对外网，不收钥匙。

绑定 127.0.0.1。关这个窗口即停。
直接打开 index.html 也能玩。
"""

from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765

FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/xiaoche.css": ("xiaoche.css", "text/css; charset=utf-8"),
    "/xiaoche.js": ("xiaoche.js", "text/javascript; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?", 1)[0]))

    def _send(self, code: int, ctype: str, payload: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        item = FILES.get(self.path.split("?", 1)[0])
        if not item:
            self._send(404, "text/plain; charset=utf-8", "没有。".encode("utf-8"))
            return
        name, ctype = item
        path = ROOT / name
        self._send(200, ctype, path.read_bytes())

    def do_POST(self) -> None:
        self._send(404, "text/plain; charset=utf-8", "没有。".encode("utf-8"))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("本地页：http://%s:%s/" % (HOST, PORT), flush=True)
    print("只本机。不接 API。关这个窗口即停。", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

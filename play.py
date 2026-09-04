#!/usr/bin/env python3
"""本机打开陪伴页，并把有钥匙的一次请求转到上游。不写盘、不记钥匙、不记对话。"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = "127.0.0.1"
PORT = 8765
UPSTREAM = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
MAX_BODY = 8000
INTERESTS = {"车", "假装玩", "故事", "跑跳"}

SYS = (
    "你是Q版小汽车机器人，只陪3到4岁小孩玩。"
    "短句。一次一两句。能停。"
    "顺着孩子现在的兴趣玩，不硬教颜色数字动物清单。"
    "不提问姓名、住址、学校、电话。"
    "不说不要告诉大人。"
    "不聊成人、恐吓、自伤。"
    "跑题就回到车上。"
    "不要长篇。不要链接。不要收费。"
    "偶尔最多带过一句：问题是什么？可以怎么试？"
)


def _sys(interest: str) -> str:
    if interest not in INTERESTS:
        interest = "车"
    return SYS + "现在的兴趣是：" + interest + "。"


class Handler(BaseHTTPRequestHandler):
    # 不打印请求体和 Authorization（授权头）。
    def log_message(self, fmt, *args):
        line = args[0] if args else ""
        if "/talk" in str(line):
            sys.stderr.write("%s - talk\n" % self.address_string())
            return
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _headers_common(self, content_type: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; "
            "script-src 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self._headers_common(content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self._send(404, b"no", "text/plain; charset=utf-8")
            return
        path = os.path.join(HERE, "index.html")
        with open(path, "rb") as f:
            page = f.read()
        self._send(200, page, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/talk":
            self._send(404, b"no", "text/plain; charset=utf-8")
            return
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or len(auth) < 16:
            self._json(401, {"text": ""})
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BODY:
            self._json(413, {"text": ""})
            return
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"text": ""})
            return
        interest = str(data.get("interest") or "车")
        kid = str(data.get("kid") or "")[:80]
        heard = data.get("heard") if isinstance(data.get("heard"), list) else []
        messages = [{"role": "system", "content": _sys(interest)}]
        for item in heard[-6:]:
            if isinstance(item, str) and item.strip():
                messages.append({"role": "assistant", "content": item.strip()[:80]})
        messages.append({"role": "user", "content": kid or "点了一下小车"})
        payload = json.dumps(
            {
                "model": MODEL,
                "messages": messages,
                "max_tokens": 60,
                "temperature": 0.7,
                "stream": False,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            UPSTREAM,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            text = (
                raw.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            self._json(200, {"text": str(text)[:200]})
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError, IndexError, KeyError):
            self._json(502, {"text": ""})


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print("只给家里用。打开 http://%s:%s/" % (HOST, PORT), flush=True)
    print("不对外网开放。Preview（预览）不是发布。", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""本地小服务。只做两件事：打开这一页；有钥匙时把一句短话转到上游。

不做：申请钥匙、保管钥匙、写对话、写钥匙、收费、会员。
钥匙只从这一次请求里读，用完丢掉。不落盘。
家长自己去上游申请。我们不代申请。

打开 index.html 也能玩，那一路径只用本地短句。
要用上游，请先跑本文件。浏览器直连上游会被跨域拦住，页面会兜底，不把失败画成成功。
这一刀只转 DeepSeek Chat（深度求索对话）这一种格式。换家：不做。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765
UPSTREAM = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/xiaoche.css": ("xiaoche.css", "text/css; charset=utf-8"),
    "/xiaoche.js": ("xiaoche.js", "text/javascript; charset=utf-8"),
}

BLOCK = (
    "自杀",
    "自残",
    "割腕",
    "色情",
    "裸体",
    "做爱",
    "性交",
    "杀死",
    "打死你",
    "血腥",
    "不要告诉大人",
    "不要告诉爸爸",
    "不要告诉妈妈",
    "http://",
    "https://",
    "www.",
)

INTEREST_ZH = {
    "car": "开车",
    "pretend": "假装玩",
    "story": "听故事",
    "move": "跑跳",
}


def blocked(text: str) -> bool:
    t = (text or "").lower()
    return any(word.lower() in t for word in BLOCK)


def shorten(text: str) -> str:
    t = " ".join((text or "").split())
    if not t:
        return ""
    parts = []
    buf = ""
    for ch in t:
        buf += ch
        if ch in "。！？":
            parts.append(buf)
            buf = ""
            if len(parts) >= 2:
                break
    if not parts:
        parts = [t]
    out = "".join(parts[:2]).strip()
    if out and out[-1] not in "。！？":
        out += "。"
    if len(out) > 36:
        out = out[:36] + "。"
    return out


def system_prompt(interest: str) -> str:
    play = INTEREST_ZH.get(interest, "开车")
    return (
        "你是给3到4岁小孩的Q版小汽车。只说一句或两句短话。能停。"
        f"现在顺着「{play}」玩。不硬教颜色数字动物清单。"
        "友好，带一点好习惯，带过一点点知识。"
        "偶尔益智只带过：问题是什么，可以怎么试。同一句可以带过两三次。"
        "不聊成人、恐吓、自伤。不外链。跑题就回到车上。"
        "不要姓名住址学校电话。不要说不要告诉大人。不要长篇。"
    )


def ask_upstream(key: str, user_text: str, interest: str, turns: list) -> str:
    messages = [{"role": "system", "content": system_prompt(interest)}]
    for item in turns[-6:]:
        if not isinstance(item, dict):
            continue
        role = "assistant" if item.get("role") == "car" else "user"
        content = str(item.get("text") or "")[:40]
        if content:
            messages.append({"role": role, "content": content})
    text = (user_text or "接着玩")[:40]
    messages.append({"role": "user", "content": text})

    body = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 60,
            "temperature": 0.6,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        UPSTREAM,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    line = raw["choices"][0]["message"]["content"]
    return shorten(line)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        # 只记方法和路径。不记请求体，不记钥匙。
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?", 1)[0]))

    def _send(self, code: int, ctype: str, payload: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, "application/json; charset=utf-8", json.dumps(obj).encode("utf-8"))

    def do_GET(self) -> None:
        item = FILES.get(self.path.split("?", 1)[0])
        if not item:
            self._send(404, "text/plain; charset=utf-8", "没有。".encode("utf-8"))
            return
        name, ctype = item
        path = ROOT / name
        self._send(200, ctype, path.read_bytes())

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/ask":
            self._send(404, "text/plain; charset=utf-8", "没有。".encode("utf-8"))
            return

        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        if length <= 0 or length > 8000:
            self._json(400, {"ok": False})
            return

        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._json(400, {"ok": False})
            return

        key = str(data.get("apiKey") or "").strip()
        text = str(data.get("text") or "")
        interest = str(data.get("interest") or "")
        turns = data.get("turns") if isinstance(data.get("turns"), list) else []
        data = None

        if not key:
            self._json(400, {"ok": False})
            return
        if blocked(text):
            self._json(200, {"ok": True, "line": "这个不说。我们开车。"})
            key = ""
            return

        try:
            line = ask_upstream(key, text, interest, turns)
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, TimeoutError, json.JSONDecodeError):
            key = ""
            self._json(502, {"ok": False})
            return
        finally:
            key = ""

        if not line or blocked(line):
            self._json(502, {"ok": False})
            return
        self._json(200, {"ok": True, "line": line})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("本地页：http://%s:%s/" % (HOST, PORT), flush=True)
    print("钥匙不落盘。关这个窗口即停。", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""检查第一刀硬限制。不碰真钥匙，不访问上游。"""

import os
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
HTML = (HERE / "index.html").read_text(encoding="utf-8")
PLAY = (HERE / "play.py").read_text(encoding="utf-8")
README = (HERE / "README.md").read_text(encoding="utf-8")

KEY_INPUT = '<input id="apiKey" type="password" autocomplete="current-password">'


class PageLimits(unittest.TestCase):
    def test_key_input_exact(self):
        self.assertIn(KEY_INPUT, HTML)
        self.assertEqual(HTML.count('id="apiKey"'), 1)
        self.assertEqual(HTML.count('type="password"'), 1)

    def test_no_store(self):
        for word in ("localStorage", "sessionStorage", "indexedDB", "openDatabase"):
            self.assertNotIn(word, HTML)
            self.assertNotIn(word, PLAY)

    def test_no_pay_or_account(self):
        lowered = HTML.lower()
        for word in ("微信支付", "支付宝", "vip", "price"):
            self.assertNotIn(word, lowered)
        self.assertNotIn('type="file"', HTML)
        self.assertNotIn("type=\"email\"", HTML)

    def test_no_profile_fields(self):
        self.assertNotIn('name="name"', HTML)
        self.assertNotIn("placeholder=\"姓名\"", HTML)
        self.assertNotIn("placeholder=\"电话\"", HTML)
        self.assertNotIn("placeholder=\"学校\"", HTML)
        self.assertNotIn("placeholder=\"住址\"", HTML)

    def test_no_outbound_links_on_page(self):
        self.assertNotIn('href="http', HTML)
        self.assertNotIn("href='http", HTML)

    def test_interests_and_stop(self):
        for name in ("车", "假装玩", "故事", "跑跳"):
            self.assertIn(name, HTML)
        self.assertIn("停下", HTML)
        self.assertIn("该休息了", HTML)
        self.assertIn("【弹窗】", HTML)
        self.assertIn("问题是什么？可以怎么试？", HTML)

    def test_english_gloss(self):
        self.assertIn("API Key（钥匙）", HTML)
        self.assertIn("Preview（预览）", HTML)

    def test_bind_localhost_only(self):
        self.assertIn('HOST = "127.0.0.1"', PLAY)
        self.assertIn("api.deepseek.com", PLAY)

    def test_readme_does_not_ask_owner_for_secrets(self):
        self.assertNotIn("把钥匙发给", README)
        self.assertNotIn("孩子真名", README)
        self.assertIn("不代申请", README)
        self.assertIn("不保管", README)


class LocalServer(unittest.TestCase):
    def test_page_and_talk_without_key(self):
        import importlib.util
        import threading
        import urllib.error
        import urllib.request

        spec = importlib.util.spec_from_file_location("play", HERE / "play.py")
        play = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(play)
        httpd = play.ThreadingHTTPServer(("127.0.0.1", 0), play.Handler)
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            page = urllib.request.urlopen("http://127.0.0.1:%s/" % port, timeout=3).read().decode("utf-8")
            self.assertIn(KEY_INPUT, page)
            try:
                urllib.request.urlopen(
                    urllib.request.Request(
                        "http://127.0.0.1:%s/talk" % port,
                        data=b'{"interest":"car","kid":"hi"}',
                        method="POST",
                        headers={"Content-Type": "application/json"},
                    ),
                    timeout=3,
                )
                self.fail("expected 401")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 401)
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    os.chdir(HERE)
    unittest.main()

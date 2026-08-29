from __future__ import annotations

import hashlib
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from regen_promptos.byok import BYOKConfig, BYOKProvider, build_byok_plan
from regen_promptos.byok_runner import (
    BYOKRunError,
    NoRedirect,
    run_byok_plan,
    validate_redirect_target,
)


def _source_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class _Handler(BaseHTTPRequestHandler):
    last_auth = None
    redirect_to = None

    def log_message(self, *args):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _Handler.last_auth = self.headers.get("Authorization")
        if _Handler.redirect_to:
            self.send_response(302)
            self.send_header("Location", _Handler.redirect_to)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        payload = {
            "id": "resp_test_1",
            "output": [
                {"content": [{"type": "output_text", "text": "hello from mock"}]}
            ],
            "usage": {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7},
        }
        data = json.dumps(payload).encode()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class BYOKRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def config(self, **overrides):
        raw = {
            "provider": "openai",
            "model": "gpt-test",
            "endpoint": f"http://127.0.0.1:{self.port}/v1/responses",
            "provider_key_env": "OPENAI_API_KEY",
            "promptos_credential_env": "PROMPTOS_ACCESS_TOKEN",
            "control_plane_url_env": "PROMPTOS_CONTROL_PLANE_URL",
            "require_promptos_credential": False,
            "require_control_plane_authorization": False,
            **overrides,
        }
        return BYOKConfig.from_dict(raw)

    def package(self):
        source = "Say hello."
        return {
            "source_sha256": _source_hash(source),
            "runtime_prompt": "Compiled: Say hello.",
            "selected_modules": ["operation:create"],
        }

    def env(self):
        return {
            "OPENAI_API_KEY": "provider-secret-value",
            "PROMPTOS_ACCESS_TOKEN": "promptos-secret-value",
            "PROMPTOS_CONTROL_PLANE_URL": "https://control.example.com",
        }

    def plan(self, config=None, environ=None):
        config = config or self.config()
        environ = environ or self.env()
        if config.provider is BYOKProvider.OPENAI:
            config = self.config(
                provider="custom",
                endpoint=config.endpoint,
                provider_key_env="OPENAI_API_KEY",
                allow_custom_endpoint=True,
            )
        return build_byok_plan(self.package(), config, environ), config

    def test_validate_redirect_target_rejects_foreign_host(self):
        with self.assertRaises(BYOKRunError):
            validate_redirect_target(
                "https://evil.example/x", allowed_hosts=("api.openai.com",)
            )

    def test_validate_redirect_target_accepts_allowlisted(self):
        url = validate_redirect_target(
            "https://api.openai.com/v1/x", allowed_hosts=("api.openai.com",)
        )
        self.assertEqual(url, "https://api.openai.com/v1/x")

    def test_no_redirect_handler_refuses(self):
        import urllib.request
        req = urllib.request.Request("http://example.com")
        with self.assertRaises(BYOKRunError):
            NoRedirect().redirect_request(
                req, None, 302, "Found", {}, "https://evil.example/"
            )

    def test_run_succeeds_and_redacts_key(self):
        _Handler.redirect_to = None
        _Handler.last_auth = None
        plan, config = self.plan()
        result = run_byok_plan(
            plan, config, "Say hello.", environ=self.env(), persist_output=False
        )
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.outcome, "SUCCEEDED")
        self.assertEqual(result.output_text, "hello from mock")
        self.assertIsNotNone(result.output_sha256)
        self.assertEqual(result.provider_usage.get("total_tokens"), 7)
        serialized = json.dumps(result.to_dict())
        self.assertNotIn("provider-secret-value", serialized)
        self.assertNotIn("promptos-secret-value", serialized)
        self.assertEqual(_Handler.last_auth, "Bearer provider-secret-value")

    def test_failed_receipt_on_transport_error(self):
        _Handler.redirect_to = None
        bad = self.config(endpoint="http://127.0.0.1:1/nope")
        plan = build_byok_plan(self.package(), bad, self.env())
        result = run_byok_plan(
            plan, bad, "Say hello.", environ=self.env(), persist_output=False
        )
        self.assertEqual(result.outcome, "FAILED")
        self.assertIsNotNone(result.error)
        serialized = json.dumps(result.receipt)
        self.assertNotIn("provider-secret-value", serialized)

    def test_response_byte_cap(self):
        class BigHandler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                return
            def do_POST(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"x" * 200_000)

        srv = HTTPServer(("127.0.0.1", 0), BigHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            cfg = self.config(
                provider="custom",
                endpoint=f"http://127.0.0.1:{port}/",
                provider_key_env="OPENAI_API_KEY",
                allow_custom_endpoint=True,
            )
            plan = build_byok_plan(self.package(), cfg, self.env())
            with self.assertRaises(BYOKRunError):
                run_byok_plan(
                    plan, cfg, "hi", environ=self.env(),
                    persist_output=False, max_response_bytes=1024,
                )
        finally:
            srv.shutdown(); srv.server_close()


if __name__ == "__main__":
    unittest.main()

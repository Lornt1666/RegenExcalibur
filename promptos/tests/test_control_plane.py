"""Deterministic tests for the v4.4 in-memory control-plane stub."""

from __future__ import annotations

import time
import unittest

from regen_promptos.byok import build_authorization_request, byok_config_template
from regen_promptos.byok import BYOKConfig
from regen_promptos.control_plane import (
    RESERVATION_TTL_S,
    ControlPlaneError,
    InMemoryControlPlane,
)


class ControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cp = InMemoryControlPlane()
        self.account = "acct_test"
        self.token = self.cp.register_account(self.account)
        self.config = BYOKConfig.from_dict(byok_config_template_custom())
        self.package = {
            "source_sha256": "a" * 64,
            "runtime_prompt": "hello",
            "selected_modules": [],
        }

    def test_authorize_settle_cancel_happy_path(self) -> None:
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-1"
        )
        res = self.cp.authorize(self.token, auth, idempotency_key="job-1")
        self.assertEqual(res["status"], "RESERVED")
        self.assertFalse(res["provider_key_included"])
        settled = self.cp.settle(
            self.token, res["reservation_id"],
            provider_outcome="SUCCEEDED",
            provider_request_id="req_1",
            output_sha256="b" * 64,
            idempotency_key="job-1-settle",
        )
        self.assertEqual(settled["status"], "SETTLED")
        self.assertEqual(len(self.cp.ledger()), 2)

    def test_authorize_is_idempotent(self) -> None:
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-2"
        )
        a = self.cp.authorize(self.token, auth, idempotency_key="job-2")
        b = self.cp.authorize(self.token, auth, idempotency_key="job-2")
        self.assertEqual(a["reservation_id"], b["reservation_id"])
        self.assertEqual(len(self.cp.ledger()), 1)

    def test_failed_provider_cancels_not_settles(self) -> None:
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-3"
        )
        res = self.cp.authorize(self.token, auth, idempotency_key="job-3")
        out = self.cp.settle(
            self.token, res["reservation_id"],
            provider_outcome="FAILED",
            idempotency_key="job-3-settle",
        )
        self.assertEqual(out["status"], "CANCELLED")

    def test_expired_reservation_refuses_settlement(self) -> None:
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-4"
        )
        res = self.cp.authorize(self.token, auth, idempotency_key="job-4")
        res_obj = self.cp._reservations[res["reservation_id"]]
        res_obj.expires_at = time.time() - 1
        with self.assertRaises(ControlPlaneError):
            self.cp.settle(
                self.token, res["reservation_id"],
                provider_outcome="SUCCEEDED",
                idempotency_key="job-4-settle",
            )
        self.assertEqual(res_obj.status, "EXPIRED")

    def test_rejects_provider_key_and_raw_prompt(self) -> None:
        bad = {"api_key": "sk-secret", "runtime_prompt": "leak me"}
        with self.assertRaises(ControlPlaneError):
            self.cp.authorize(self.token, bad, idempotency_key="bad-1")

    def test_ledger_is_append_only_and_hash_chained(self) -> None:
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-5"
        )
        res = self.cp.authorize(self.token, auth, idempotency_key="job-5")
        self.cp.settle(
            self.token, res["reservation_id"],
            provider_outcome="SUCCEEDED",
            idempotency_key="job-5-settle",
        )
        ledger = self.cp.ledger()
        self.assertEqual(len(ledger), 2)
        self.assertEqual(ledger[0]["prev_hash"], "0" * 64)
        self.assertEqual(ledger[1]["prev_hash"], ledger[0]["entry_hash"])
        self.assertNotEqual(ledger[0]["entry_hash"], ledger[1]["entry_hash"])

    def test_revoked_token_denied(self) -> None:
        self.cp.revoke_token(self.token)
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-6"
        )
        with self.assertRaises(ControlPlaneError):
            self.cp.authorize(self.token, auth, idempotency_key="job-6")

    def test_cannot_cancel_settled(self) -> None:
        auth = build_authorization_request(
            self.package, self.config, idempotency_key="job-7"
        )
        res = self.cp.authorize(self.token, auth, idempotency_key="job-7")
        self.cp.settle(
            self.token, res["reservation_id"],
            provider_outcome="SUCCEEDED",
            idempotency_key="job-7-settle",
        )
        with self.assertRaises(ControlPlaneError):
            self.cp.cancel(self.token, res["reservation_id"], idempotency_key="job-7-cancel")


def byok_config_template_custom():
    raw = byok_config_template("custom")
    raw["endpoint"] = "https://provider.example/v1/chat"
    raw["allow_custom_endpoint"] = True
    return raw

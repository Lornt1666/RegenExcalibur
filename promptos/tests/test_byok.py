from __future__ import annotations

import hashlib
import json
import unittest

from regen_promptos.byok import (
    BYOKConfig,
    BYOKError,
    BYOKProvider,
    build_authorization_request,
    build_byok_plan,
    byok_config_template,
    create_byok_receipt,
    inspect_byok_environment,
    quote_promptos_service_units,
)


class BYOKTests(unittest.TestCase):
    def config(self, **overrides) -> BYOKConfig:
        raw = {
            "provider": "openai",
            "model": "provider-model-id",
            "endpoint": "https://api.openai.com/v1/responses",
            "provider_key_env": "OPENAI_API_KEY",
            "promptos_credential_env": "PROMPTOS_ACCESS_TOKEN",
            "control_plane_url_env": "PROMPTOS_CONTROL_PLANE_URL",
            **overrides,
        }
        return BYOKConfig.from_dict(raw)

    def package(self) -> dict:
        source = "Design a safe BYOK execution plan."
        return {
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "runtime_prompt": "Compiled PromptOS runtime prompt.",
            "selected_modules": [
                "operation:create",
                "software",
                "professional_boundaries",
            ],
        }

    def env(self) -> dict[str, str]:
        return {
            "OPENAI_API_KEY": "provider-secret-value",
            "PROMPTOS_ACCESS_TOKEN": "promptos-secret-value",
            "PROMPTOS_CONTROL_PLANE_URL": "https://control.example.com",
        }

    def test_config_rejects_literal_secret(self) -> None:
        with self.assertRaises(BYOKError):
            BYOKConfig.from_dict(
                {
                    "provider": "openai",
                    "model": "x",
                    "endpoint": "https://api.openai.com/v1/responses",
                    "provider_key_env": "OPENAI_API_KEY",
                    "api_key": "must-not-be-here",
                }
            )

    def test_credentials_must_use_distinct_env_vars(self) -> None:
        with self.assertRaises(BYOKError):
            self.config(promptos_credential_env="OPENAI_API_KEY")

    def test_official_provider_host_is_allowlisted(self) -> None:
        with self.assertRaises(BYOKError):
            self.config(endpoint="https://attacker.example/v1/responses")

    def test_official_provider_auth_override_rejected(self) -> None:
        with self.assertRaises(BYOKError):
            self.config(auth_header="x-custom")

    def test_custom_endpoint_requires_explicit_review_flag(self) -> None:
        with self.assertRaises(BYOKError):
            BYOKConfig.from_dict(
                {
                    "provider": "custom",
                    "model": "x",
                    "endpoint": "https://provider.example/v1",
                    "provider_key_env": "CUSTOM_PROVIDER_API_KEY",
                }
            )

    def test_endpoint_rejects_secret_query_parameter(self) -> None:
        with self.assertRaises(BYOKError):
            self.config(
                endpoint="https://api.openai.com/v1/responses?api_key=not-safe"
            )

    def test_string_false_is_not_truthy(self) -> None:
        config = self.config(
            require_promptos_credential="false",
            require_control_plane_authorization="false",
        )
        self.assertFalse(config.require_promptos_credential)
        self.assertFalse(config.require_control_plane_authorization)

    def test_environment_report_never_exposes_values(self) -> None:
        report = inspect_byok_environment(self.config(), self.env())
        serialized = json.dumps(report)
        self.assertEqual(report["status"], "PASS")
        for value in self.env().values():
            self.assertNotIn(value, serialized)

    def test_missing_promptos_credential_fails_closed(self) -> None:
        report = inspect_byok_environment(
            self.config(),
            {
                "OPENAI_API_KEY": "provider-secret",
                "PROMPTOS_CONTROL_PLANE_URL": "https://control.example.com",
            },
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "MISSING_PROMPTOS_CREDENTIAL_ENV:PROMPTOS_ACCESS_TOKEN",
            report["blockers"],
        )

    def test_missing_control_plane_url_fails_closed(self) -> None:
        report = inspect_byok_environment(
            self.config(),
            {
                "OPENAI_API_KEY": "provider-secret",
                "PROMPTOS_ACCESS_TOKEN": "promptos-secret",
            },
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn(
            "MISSING_CONTROL_PLANE_URL_ENV:PROMPTOS_CONTROL_PLANE_URL",
            report["blockers"],
        )

    def test_control_plane_url_rejects_http(self) -> None:
        env = self.env()
        env["PROMPTOS_CONTROL_PLANE_URL"] = "http://control.example.com"
        report = inspect_byok_environment(self.config(), env)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(
            any(item.startswith("INVALID_CONTROL_PLANE_URL:") for item in report["blockers"])
        )

    def test_plan_keeps_provider_key_local(self) -> None:
        plan = build_byok_plan(self.package(), self.config(), self.env())
        serialized = json.dumps(plan)
        self.assertEqual(plan["status"], "PASS")
        self.assertFalse(
            plan["credential_boundaries"]["provider_key"]["sent_to_promptos"]
        )
        self.assertEqual(
            plan["provider"]["auth_value_template"], "Bearer ${OPENAI_API_KEY}"
        )
        for value in self.env().values():
            self.assertNotIn(value, serialized)

    def test_anthropic_static_version_header(self) -> None:
        config = BYOKConfig.from_dict(byok_config_template(BYOKProvider.ANTHROPIC))
        env = {
            "ANTHROPIC_API_KEY": "provider-secret",
            "PROMPTOS_ACCESS_TOKEN": "promptos-secret",
            "PROMPTOS_CONTROL_PLANE_URL": "https://control.example.com",
        }
        plan = build_byok_plan(self.package(), config, env)
        self.assertEqual(
            plan["provider"]["static_headers"]["anthropic-version"],
            "2023-06-01",
        )

    def test_plan_can_report_blocked_without_throwing(self) -> None:
        plan = build_byok_plan(
            self.package(), self.config(), {}, require_ready=False
        )
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertFalse(plan["environment"]["ready"])

    def test_service_units_are_deterministic_and_provider_cost_excluded(self) -> None:
        quote = quote_promptos_service_units(self.package())
        self.assertEqual(quote["total_units"], 3)
        self.assertFalse(quote["provider_model_usage_included"])
        self.assertFalse(quote["currency_value_assigned"])

    def test_authorization_request_excludes_prompt_and_keys(self) -> None:
        request = build_authorization_request(
            self.package(), self.config(), idempotency_key="job-123"
        )
        serialized = json.dumps(request)
        self.assertFalse(request["provider_key_included"])
        self.assertFalse(request["runtime_prompt_included"])
        self.assertFalse(request["source_material_included"])
        self.assertNotIn("Compiled PromptOS runtime prompt.", serialized)
        self.assertNotIn("OPENAI_API_KEY", serialized)

    def test_receipt_redacts_sensitive_metadata(self) -> None:
        plan = build_byok_plan(self.package(), self.config(), self.env())
        receipt = create_byok_receipt(
            plan,
            outcome="SUCCEEDED",
            authorization_id="auth_public_identifier",
            settlement_id="settle_public_identifier",
            provider_request_id="req_public_identifier",
            output_sha256="a" * 64,
            metadata={
                "authorization": "Bearer secret",
                "nested": {"api_key": "secret", "safe": "value"},
            },
        )
        self.assertEqual(receipt["metadata"]["authorization"], "[REDACTED]")
        self.assertEqual(receipt["metadata"]["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(receipt["metadata"]["nested"]["safe"], "value")
        self.assertRegex(receipt["receipt_sha256"], r"^[0-9a-f]{64}$")

    def test_receipt_rejects_known_secret_in_innocent_field(self) -> None:
        plan = build_byok_plan(self.package(), self.config(), self.env())
        with self.assertRaises(BYOKError):
            create_byok_receipt(
                plan,
                outcome="FAILED",
                metadata={"note": "provider-secret-value"},
                known_secrets=("provider-secret-value",),
            )

    def test_config_templates_contain_placeholders_not_secrets(self) -> None:
        openai = byok_config_template(BYOKProvider.OPENAI)
        google = byok_config_template(BYOKProvider.GOOGLE)
        self.assertEqual(openai["provider_key_env"], "OPENAI_API_KEY")
        self.assertNotIn("api_key", openai)
        self.assertEqual(openai["model"], "SET_PROVIDER_MODEL_ID")
        self.assertEqual(google["provider_key_env"], "GEMINI_API_KEY")
        self.assertIn(":generateContent", google["endpoint"])


if __name__ == "__main__":
    unittest.main()

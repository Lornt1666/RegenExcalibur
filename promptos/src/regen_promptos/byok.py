"""Provider-key-safe BYOK planning for RegenExcalibur PromptOS.

This module deliberately does not perform live provider or payment network calls.
It validates and compiles a secret-free execution plan in which:

* the customer's model-provider key remains on the customer's device;
* the PromptOS access credential is sent only to the PromptOS control plane;
* PromptOS meters its orchestration service separately from provider usage; and
* provider execution, settlement, and completion remain distinct evidence states.

A later runtime may consume this plan, but it must preserve the credential and
receipt invariants defined here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
import re
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit


class BYOKError(ValueError):
    """Raised when a BYOK configuration or execution plan is unsafe or invalid."""


class BYOKProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    CUSTOM = "custom"


class BYOKExecutionMode(str, Enum):
    LOCAL_DIRECT = "LOCAL_DIRECT"


_PROVIDER_PROFILES: dict[BYOKProvider, dict[str, object]] = {
    BYOKProvider.OPENAI: {
        "hosts": ("api.openai.com",),
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "static_headers": {},
    },
    BYOKProvider.ANTHROPIC: {
        "hosts": ("api.anthropic.com",),
        "auth_header": "x-api-key",
        "auth_prefix": "",
        "static_headers": {"anthropic-version": "2023-06-01"},
    },
    BYOKProvider.GOOGLE: {
        "hosts": (
            "generativelanguage.googleapis.com",
            "aiplatform.googleapis.com",
        ),
        "auth_header": "x-goog-api-key",
        "auth_prefix": "",
        "static_headers": {},
    },
    BYOKProvider.CUSTOM: {
        "hosts": (),
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "static_headers": {},
    },
}

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_QUERY_SECRET_NAMES = {
    "api_key",
    "apikey",
    "key",
    "secret",
    "token",
    "access_token",
    "password",
}
_FORBIDDEN_LITERAL_CONFIG_KEYS = {
    "api_key",
    "apikey",
    "provider_key",
    "secret",
    "password",
    "access_token",
    "promptos_access_token",
}
_SENSITIVE_METADATA_PARTS = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "authorization",
    "access_token",
    "provider_key",
    "cookie",
)

_MODULE_UNIT_WEIGHTS = {
    "research": 1,
    "software": 1,
    "operations": 1,
    "business": 1,
    "creative": 1,
    "education": 1,
    "innovation": 1,
    "definitive_completion": 1,
    "built_environment": 2,
    "professional_boundaries": 1,
}


def _require_env_name(value: str, field_name: str) -> str:
    candidate = str(value or "").strip()
    if not _ENV_NAME.fullmatch(candidate):
        raise BYOKError(
            f"{field_name} must be an environment-variable name, not a secret value"
        )
    return candidate


def _reject_literal_secrets(raw: Mapping[str, Any]) -> None:
    for key in raw:
        normalized = str(key).strip().lower().replace("-", "_")
        if normalized in _FORBIDDEN_LITERAL_CONFIG_KEYS:
            raise BYOKError(
                f"{key!r} is not accepted; configure only the environment-variable name"
            )


def _coerce_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    raise BYOKError(f"{field_name} must be a boolean")


def _validate_https_url(
    value: str,
    *,
    field_name: str,
    forbid_query: bool = False,
) -> None:
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise BYOKError(f"{field_name} must use HTTPS")
    if not parsed.hostname:
        raise BYOKError(f"{field_name} must contain a hostname")
    if parsed.username or parsed.password:
        raise BYOKError(f"{field_name} must not contain embedded credentials")
    if parsed.fragment:
        raise BYOKError(f"{field_name} must not contain a fragment")
    if forbid_query and parsed.query:
        raise BYOKError(f"{field_name} must not contain a query string")


@dataclass(frozen=True)
class BYOKConfig:
    provider: BYOKProvider
    model: str
    endpoint: str
    provider_key_env: str
    promptos_credential_env: str = "PROMPTOS_ACCESS_TOKEN"
    control_plane_url_env: str = "PROMPTOS_CONTROL_PLANE_URL"
    require_promptos_credential: bool = True
    require_control_plane_authorization: bool = True
    allow_custom_endpoint: bool = False
    execution_mode: BYOKExecutionMode = BYOKExecutionMode.LOCAL_DIRECT
    auth_header: str | None = None
    auth_prefix: str | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "BYOKConfig":
        if not isinstance(raw, Mapping):
            raise BYOKError("BYOK configuration must be an object")
        _reject_literal_secrets(raw)

        try:
            provider = BYOKProvider(str(raw.get("provider", "")).strip().lower())
        except ValueError as exc:
            allowed = ", ".join(item.value for item in BYOKProvider)
            raise BYOKError(f"provider must be one of: {allowed}") from exc

        try:
            execution_mode = BYOKExecutionMode(
                str(raw.get("execution_mode", "LOCAL_DIRECT")).strip().upper()
            )
        except ValueError as exc:
            raise BYOKError("only LOCAL_DIRECT execution is supported") from exc

        model = str(raw.get("model", "")).strip()
        if not model:
            raise BYOKError("model is required")

        endpoint = str(raw.get("endpoint", "")).strip()
        provider_key_env = _require_env_name(
            str(raw.get("provider_key_env", "")), "provider_key_env"
        )
        promptos_credential_env = _require_env_name(
            str(raw.get("promptos_credential_env", "PROMPTOS_ACCESS_TOKEN")),
            "promptos_credential_env",
        )
        control_plane_url_env = _require_env_name(
            str(raw.get("control_plane_url_env", "PROMPTOS_CONTROL_PLANE_URL")),
            "control_plane_url_env",
        )
        if len({provider_key_env, promptos_credential_env, control_plane_url_env}) != 3:
            raise BYOKError(
                "provider, PromptOS credential, and control-plane URL must use distinct environment variables"
            )

        config = cls(
            provider=provider,
            model=model,
            endpoint=endpoint,
            provider_key_env=provider_key_env,
            promptos_credential_env=promptos_credential_env,
            control_plane_url_env=control_plane_url_env,
            require_promptos_credential=_coerce_bool(
                raw.get("require_promptos_credential", True),
                "require_promptos_credential",
            ),
            require_control_plane_authorization=_coerce_bool(
                raw.get("require_control_plane_authorization", True),
                "require_control_plane_authorization",
            ),
            allow_custom_endpoint=_coerce_bool(
                raw.get("allow_custom_endpoint", False),
                "allow_custom_endpoint",
            ),
            execution_mode=execution_mode,
            auth_header=(
                str(raw["auth_header"]).strip()
                if raw.get("auth_header") is not None
                else None
            ),
            auth_prefix=(
                str(raw["auth_prefix"])
                if raw.get("auth_prefix") is not None
                else None
            ),
        )
        validate_byok_config(config)
        return config


def validate_byok_config(config: BYOKConfig) -> None:
    if config.execution_mode is not BYOKExecutionMode.LOCAL_DIRECT:
        raise BYOKError("provider-proxy execution is not enabled in this release")

    _validate_https_url(config.endpoint, field_name="provider endpoint")
    parsed = urlsplit(config.endpoint)

    query_names = {name.lower() for name, _ in parse_qsl(parsed.query)}
    if query_names.intersection(_QUERY_SECRET_NAMES):
        raise BYOKError("provider credentials must not be placed in the endpoint query")

    profile = _PROVIDER_PROFILES[config.provider]
    allowed_hosts = tuple(str(host) for host in profile["hosts"])
    hostname = (parsed.hostname or "").lower()

    if config.provider is BYOKProvider.CUSTOM:
        if not config.allow_custom_endpoint:
            raise BYOKError(
                "custom endpoints require allow_custom_endpoint=true after review"
            )
    elif hostname not in allowed_hosts:
        raise BYOKError(
            f"{config.provider.value} endpoint host {hostname!r} is not allowlisted"
        )

    if config.provider is not BYOKProvider.CUSTOM and (
        config.auth_header is not None or config.auth_prefix is not None
    ):
        raise BYOKError(
            "auth header overrides are allowed only for reviewed custom providers"
        )

    header = config.auth_header or str(profile["auth_header"])
    if not header or any(character in header for character in "\r\n:"):
        raise BYOKError("auth_header is invalid")


def inspect_byok_environment(
    config: BYOKConfig,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    provider_present = bool(env.get(config.provider_key_env))
    promptos_present = bool(env.get(config.promptos_credential_env))
    control_plane_present = bool(env.get(config.control_plane_url_env))

    blockers: list[str] = []
    if not provider_present:
        blockers.append(f"MISSING_PROVIDER_KEY_ENV:{config.provider_key_env}")
    if config.require_promptos_credential and not promptos_present:
        blockers.append(
            f"MISSING_PROMPTOS_CREDENTIAL_ENV:{config.promptos_credential_env}"
        )
    if config.require_control_plane_authorization:
        if not control_plane_present:
            blockers.append(
                f"MISSING_CONTROL_PLANE_URL_ENV:{config.control_plane_url_env}"
            )
        else:
            try:
                _validate_https_url(
                    str(env[config.control_plane_url_env]),
                    field_name="PromptOS control-plane URL",
                    forbid_query=True,
                )
            except BYOKError as exc:
                blockers.append(f"INVALID_CONTROL_PLANE_URL:{exc}")

    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "ready": not blockers,
        "provider_key": {
            "env_var": config.provider_key_env,
            "present": provider_present,
            "value_exposed": False,
        },
        "promptos_credential": {
            "env_var": config.promptos_credential_env,
            "present": promptos_present,
            "value_exposed": False,
        },
        "control_plane_url": {
            "env_var": config.control_plane_url_env,
            "present": control_plane_present,
            "value_exposed": False,
            "authorization_required": config.require_control_plane_authorization,
        },
        "blockers": blockers,
    }


def quote_promptos_service_units(prompt_package: Mapping[str, Any]) -> dict[str, Any]:
    modules = prompt_package.get("selected_modules", [])
    if not isinstance(modules, list):
        raise BYOKError("prompt package selected_modules must be an array")

    line_items = [{"reason": "base_job_authorization", "units": 1}]
    total = 1
    for module in sorted({str(item) for item in modules}):
        normalized = module.split(":", 1)[-1]
        units = _MODULE_UNIT_WEIGHTS.get(normalized, 0)
        if units:
            line_items.append({"reason": f"module:{normalized}", "units": units})
            total += units

    return {
        "unit_name": "PROMPTOS_SERVICE_UNIT",
        "total_units": total,
        "line_items": line_items,
        "currency_value_assigned": False,
        "provider_model_usage_included": False,
    }


def _runtime_prompt_hash(prompt_package: Mapping[str, Any]) -> str:
    runtime_prompt = prompt_package.get("runtime_prompt")
    if not isinstance(runtime_prompt, str) or not runtime_prompt.strip():
        raise BYOKError("prompt package must contain a non-empty runtime_prompt")
    return hashlib.sha256(runtime_prompt.encode("utf-8")).hexdigest()


def _source_hash(prompt_package: Mapping[str, Any]) -> str:
    value = prompt_package.get("source_sha256")
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise BYOKError("prompt package must contain a valid source_sha256")
    return value


def build_authorization_request(
    prompt_package: Mapping[str, Any],
    config: BYOKConfig,
    *,
    idempotency_key: str,
) -> dict[str, Any]:
    """Build a secret-free request body for a future PromptOS control plane."""
    candidate = str(idempotency_key or "").strip()
    if not candidate or len(candidate) > 255:
        raise BYOKError("idempotency_key must contain 1 to 255 characters")
    return {
        "schema_version": "1.0",
        "idempotency_key": candidate,
        "provider": config.provider.value,
        "model": config.model,
        "source_sha256": _source_hash(prompt_package),
        "runtime_prompt_sha256": _runtime_prompt_hash(prompt_package),
        "service_quote": quote_promptos_service_units(prompt_package),
        "requested_execution_mode": config.execution_mode.value,
        "provider_key_included": False,
        "runtime_prompt_included": False,
        "source_material_included": False,
    }


def build_byok_plan(
    prompt_package: Mapping[str, Any],
    config: BYOKConfig,
    environ: Mapping[str, str] | None = None,
    *,
    require_ready: bool = True,
) -> dict[str, Any]:
    validate_byok_config(config)
    environment = inspect_byok_environment(config, environ)
    if require_ready and not environment["ready"]:
        raise BYOKError("; ".join(environment["blockers"]))

    profile = _PROVIDER_PROFILES[config.provider]
    auth_header = config.auth_header or str(profile["auth_header"])
    auth_prefix = (
        config.auth_prefix
        if config.auth_prefix is not None
        else str(profile["auth_prefix"])
    )
    runtime_sha256 = _runtime_prompt_hash(prompt_package)
    source_sha256 = _source_hash(prompt_package)
    quote = quote_promptos_service_units(prompt_package)

    plan: dict[str, Any] = {
        "schema_version": "1.0",
        "architecture": "PROMPTOS_CONTROL_PLANE_LOCAL_PROVIDER_EXECUTION",
        "execution_mode": config.execution_mode.value,
        "provider": {
            "name": config.provider.value,
            "model": config.model,
            "endpoint": config.endpoint,
            "auth_header": auth_header,
            "auth_value_template": f"{auth_prefix}${{{config.provider_key_env}}}",
            "static_headers": dict(profile.get("static_headers", {})),
            "call_location": "customer_device",
        },
        "credential_boundaries": {
            "provider_key": {
                "source": "environment",
                "env_var": config.provider_key_env,
                "sent_to_promptos": False,
                "persisted_by_promptos": False,
                "logged_by_promptos": False,
                "destination": "configured_provider_endpoint_only",
            },
            "promptos_credential": {
                "source": "environment",
                "env_var": config.promptos_credential_env,
                "sent_to_provider": False,
                "destination": "promptos_control_plane_only",
            },
            "control_plane_url": {
                "source": "environment",
                "env_var": config.control_plane_url_env,
                "sent_to_provider": False,
                "value_embedded_in_plan": False,
            },
        },
        "control_plane": {
            "authorization_required": config.require_control_plane_authorization,
            "authorization_contract": "/v1/byok/authorize",
            "settlement_contract": "/v1/byok/settle",
            "cancellation_contract": "/v1/byok/cancel",
            "provider_key_allowed": False,
            "runtime_prompt_allowed": False,
            "source_material_allowed": False,
        },
        "prompt_package": {
            "source_sha256": source_sha256,
            "runtime_prompt_sha256": runtime_sha256,
            "runtime_prompt_embedded_in_plan": False,
        },
        "metering": quote,
        "environment": environment,
        "workflow": [
            "Authenticate to the PromptOS control plane with the PromptOS credential.",
            "Authorize and reserve the selected PromptOS service units.",
            "Receive or load the compiled runtime prompt without provider credentials.",
            "Resolve the provider key from the local environment in memory.",
            "Call the allowlisted provider endpoint directly from the customer device.",
            "Create a secret-free completion receipt.",
            "Settle or cancel the PromptOS service-unit reservation idempotently.",
        ],
        "security_invariants": [
            "Provider keys and PromptOS credentials are distinct.",
            "Provider keys never enter PromptOS requests, logs, receipts, or storage.",
            "Provider calls originate from the customer device.",
            "PromptOS meters orchestration value, not the customer's provider tokens.",
            "No provider call is represented as completed without provider evidence.",
            "No PromptOS charge is represented as settled without a control-plane receipt.",
        ],
        "implementation_state": "CLIENT_PREFLIGHT_IMPLEMENTED_CONTROL_PLANE_PENDING",
        "status": environment["status"],
    }

    serialized = json.dumps(plan, ensure_ascii=False, sort_keys=True)
    env = os.environ if environ is None else environ
    for env_name in (
        config.provider_key_env,
        config.promptos_credential_env,
        config.control_plane_url_env,
    ):
        secret_or_value = env.get(env_name)
        if secret_or_value and secret_or_value in serialized:
            raise BYOKError(f"value from {env_name} leaked into BYOK plan")
    return plan


def _sanitize_metadata(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _SENSITIVE_METADATA_PARTS):
                sanitized[str(key)] = "[REDACTED]"
            else:
                sanitized[str(key)] = _sanitize_metadata(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_metadata(item) for item in value]
    return value


def create_byok_receipt(
    plan: Mapping[str, Any],
    *,
    outcome: str,
    authorization_id: str | None = None,
    settlement_id: str | None = None,
    provider_request_id: str | None = None,
    output_sha256: str | None = None,
    provider_usage: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    known_secrets: tuple[str, ...] = (),
) -> dict[str, Any]:
    if outcome not in {"SUCCEEDED", "FAILED", "CANCELLED"}:
        raise BYOKError("outcome must be SUCCEEDED, FAILED, or CANCELLED")
    runtime_sha256 = (
        plan.get("prompt_package", {}).get("runtime_prompt_sha256")
        if isinstance(plan.get("prompt_package"), Mapping)
        else None
    )
    if not isinstance(runtime_sha256, str):
        raise BYOKError("plan is missing runtime_prompt_sha256")
    if output_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", output_sha256):
        raise BYOKError("output_sha256 must be a lowercase SHA-256 hex digest")

    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "architecture": plan.get("architecture"),
        "provider": (
            plan.get("provider", {}).get("name")
            if isinstance(plan.get("provider"), Mapping)
            else None
        ),
        "model": (
            plan.get("provider", {}).get("model")
            if isinstance(plan.get("provider"), Mapping)
            else None
        ),
        "runtime_prompt_sha256": runtime_sha256,
        "outcome": outcome,
        "authorization_id": authorization_id,
        "settlement_id": settlement_id,
        "provider_request_id": provider_request_id,
        "output_sha256": output_sha256,
        "provider_usage": _sanitize_metadata(provider_usage or {}),
        "metadata": _sanitize_metadata(metadata or {}),
        "assertions": {
            "provider_key_collected_by_promptos": False,
            "provider_key_persisted_by_promptos": False,
            "provider_cost_billed_to_promptos": False,
            "provider_cost_billed_to_customer_provider_account": True,
            "payment_or_entitlement_verified_by_this_local_receipt": False,
        },
    }
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    for secret in known_secrets:
        if secret and secret in serialized:
            raise BYOKError("known secret leaked into BYOK receipt")
    canonical = serialized.encode("utf-8")
    receipt["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    return receipt


def byok_config_template(provider: BYOKProvider) -> dict[str, Any]:
    defaults = {
        BYOKProvider.OPENAI: ("OPENAI_API_KEY", "https://api.openai.com/v1/responses"),
        BYOKProvider.ANTHROPIC: (
            "ANTHROPIC_API_KEY",
            "https://api.anthropic.com/v1/messages",
        ),
        BYOKProvider.GOOGLE: (
            "GEMINI_API_KEY",
            "https://generativelanguage.googleapis.com/v1beta/models/SET_PROVIDER_MODEL_ID:generateContent",
        ),
        BYOKProvider.CUSTOM: ("CUSTOM_PROVIDER_API_KEY", "https://provider.example/v1"),
    }
    provider_key_env, endpoint = defaults[provider]
    return {
        "provider": provider.value,
        "model": "SET_PROVIDER_MODEL_ID",
        "endpoint": endpoint,
        "provider_key_env": provider_key_env,
        "promptos_credential_env": "PROMPTOS_ACCESS_TOKEN",
        "control_plane_url_env": "PROMPTOS_CONTROL_PLANE_URL",
        "require_promptos_credential": True,
        "require_control_plane_authorization": True,
        "allow_custom_endpoint": provider is BYOKProvider.CUSTOM,
        "execution_mode": BYOKExecutionMode.LOCAL_DIRECT.value,
    }


__all__ = [
    "BYOKConfig",
    "BYOKError",
    "BYOKExecutionMode",
    "BYOKProvider",
    "build_authorization_request",
    "build_byok_plan",
    "byok_config_template",
    "create_byok_receipt",
    "inspect_byok_environment",
    "quote_promptos_service_units",
    "validate_byok_config",
]

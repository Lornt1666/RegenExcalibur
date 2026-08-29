"""Local BYOK provider runner for RegenExcalibur PromptOS.

Executes a secret-free BYOK plan produced by byok.py against an allowlisted
provider endpoint. The provider credential is resolved from the local
environment in memory only; it is never written to disk, logs, receipts, or
telemetry. Redirects are denied and the destination host is revalidated
immediately before credential use.

This module performs a real network call when a provider key is present. It
must be invoked only after build_byok_plan reports PASS and the customer has
authorized the run.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import time
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .byok import (
    BYOKConfig,
    BYOKError,
    BYOKProvider,
    _PROVIDER_PROFILES,
    _validate_https_url,
    build_byok_plan,
    create_byok_receipt,
    inspect_byok_environment,
)

__all__ = [
    "BYOKRunError",
    "BYOKRunResult",
    "NoRedirect",
    "run_byok_plan",
    "validate_redirect_target",
]

_MAX_RESPONSE_BYTES = 1_048_576  # 1 MiB
_DEFAULT_TIMEOUT_S = 30.0
_ALLOWED_METHODS = {"POST"}


class BYOKRunError(BYOKError):
    """Raised when a local BYOK provider run fails safely."""


class NoRedirect(HTTPRedirectHandler):
    """Refuse every redirect; the runner revalidates destinations itself."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        raise BYOKRunError(f"redirect refused: {code} -> {newurl}")

    def http_error_302(self, req, fp, code, msg, headers):  # type: ignore[override]
        return self.http_error_default(req, fp, code, msg, headers)

    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302
    http_error_308 = http_error_302


def validate_redirect_target(url: str, *, allowed_hosts: tuple[str, ...]) -> str:
    """Revalidate a candidate destination host against the allowlist.

    Returns the normalized URL on success; raises BYOKRunError otherwise.
    """
    _validate_https_url(url, field_name="redirect target")
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in allowed_hosts:
        raise BYOKRunError(
            f"redirect target host {hostname!r} is not allowlisted"
        )
    if parsed.username or parsed.password:
        raise BYOKRunError("redirect target must not contain embedded credentials")
    if parsed.query:
        names = {n.lower() for n, _ in parse_qsl(parsed.query)}
        if names & {"api_key", "apikey", "key", "secret", "token", "access_token", "password"}:
            raise BYOKRunError("redirect target must not carry secret query parameters")
    return url


def _resolve_provider_key(env_name: str, environ: Mapping[str, str]) -> str:
    value = environ.get(env_name)
    if not value:
        raise BYOKRunError(f"provider key env {env_name!r} is empty at execution time")
    return value


def _build_request(
    config: BYOKConfig,
    plan: Mapping[str, Any],
    prompt_text: str,
    provider_key: str,
) -> Request:
    profile = _PROVIDER_PROFILES[config.provider]
    auth_header = config.auth_header or str(profile["auth_header"])
    auth_prefix = (
        config.auth_prefix
        if config.auth_prefix is not None
        else str(profile["auth_prefix"])
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        auth_header: f"{auth_prefix}{provider_key}",
    }
    for key, value in dict(profile.get("static_headers", {})).items():
        headers[key] = value

    body = _provider_body(config, plan, prompt_text)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    return Request(config.endpoint, data=data, headers=headers, method="POST")


def _provider_body(
    config: BYOKConfig, plan: Mapping[str, Any], prompt_text: str
) -> dict[str, Any]:
    """Construct a provider-specific request body from the compiled prompt.

    The body contains only the compiled runtime prompt and model metadata.
    No PromptOS credentials, no service-unit data, no control-plane URLs.
    """
    if config.provider is BYOKProvider.OPENAI:
        return {
            "model": config.model,
            "input": prompt_text,
        }
    if config.provider is BYOKProvider.ANTHROPIC:
        return {
            "model": config.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt_text}],
        }
    if config.provider is BYOKProvider.GOOGLE:
        return {
            "contents": [{"parts": [{"text": prompt_text}]}],
        }
    return {"prompt": prompt_text, "model": config.model}


def _extract_output_text(config: BYOKConfig, payload: Mapping[str, Any]) -> str:
    if config.provider is BYOKProvider.OPENAI:
        for block in payload.get("output", []) or []:
            for part in block.get("content", []) or []:
                if isinstance(part, dict) and part.get("type") == "output_text":
                    return str(part.get("text", ""))
        for choice in payload.get("choices", []) or []:
            msg = choice.get("message", {})
            if isinstance(msg, dict) and msg.get("content"):
                return str(msg["content"])
        return json.dumps(payload, ensure_ascii=False)
    if config.provider is BYOKProvider.ANTHROPIC:
        blocks = payload.get("content", []) or []
        texts = [b.get("text", "") for b in blocks if isinstance(b, dict)]
        return "\n".join(texts) if texts else json.dumps(payload, ensure_ascii=False)
    if config.provider is BYOKProvider.GOOGLE:
        cands = payload.get("candidates", []) or []
        parts: list[str] = []
        for cand in cands:
            content = cand.get("content", {})
            for part in content.get("parts", []) or []:
                if "text" in part:
                    parts.append(str(part["text"]))
        return "\n".join(parts) if parts else json.dumps(payload, ensure_ascii=False)
    return json.dumps(payload, ensure_ascii=False)


def _extract_usage(config: BYOKConfig, payload: Mapping[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") or {}
    if not isinstance(usage, dict):
        return {}
    out: dict[str, Any] = {}
    for key in ("input_tokens", "prompt_tokens", "promptTokenCount",
                "output_tokens", "completion_tokens", "candidatesTokenCount",
                "total_tokens", "totalTokenCount"):
        if key in usage:
            out[key] = usage[key]
    return out


@dataclass
class BYOKRunResult:
    status: str
    outcome: str
    provider: str
    model: str
    http_status: int | None
    output_text: str
    output_sha256: str | None
    provider_usage: dict[str, Any]
    provider_request_id: str | None
    elapsed_s: float
    receipt: dict[str, Any]
    error: str | None = None
    raw_response_saved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "outcome": self.outcome,
            "provider": self.provider,
            "model": self.model,
            "http_status": self.http_status,
            "output_sha256": self.output_sha256,
            "provider_usage": self.provider_usage,
            "provider_request_id": self.provider_request_id,
            "elapsed_s": self.elapsed_s,
            "error": self.error,
            "raw_response_saved": self.raw_response_saved,
            "receipt": self.receipt,
        }


def run_byok_plan(
    plan: Mapping[str, Any],
    config: BYOKConfig,
    prompt_text: str,
    *,
    environ: Mapping[str, str] | None = None,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    max_response_bytes: int = _MAX_RESPONSE_BYTES,
    persist_output: bool = True,
    output_dir: str | None = None,
    authorization_id: str | None = None,
    settlement_id: str | None = None,
) -> BYOKRunResult:
    """Execute a validated BYOK plan against the configured provider.

    Invariants enforced:
    * provider key resolved from env in memory only
    * no redirect followed; destination revalidated before credential use
    * response bounded by max_response_bytes
    * timeout enforced
    * raw output persisted locally only when persist_output=True
    * receipt never contains the provider key or PromptOS credential
    * a FAILED receipt is emitted on any provider or transport error
    """
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise BYOKRunError("prompt_text must be a non-empty string")
    if plan.get("status") != "PASS":
        raise BYOKRunError("plan status must be PASS before execution")
    if plan.get("implementation_state") not in {
        "CLIENT_PREFLIGHT_IMPLEMENTED_CONTROL_PLANE_PENDING",
        "LOCAL_RUNNER_READY",
    }:
        raise BYOKRunError("plan is not in an executable state")

    env = os.environ if environ is None else environ
    inspection = inspect_byok_environment(config, env)
    if not inspection["ready"]:
        raise BYOKRunError("; ".join(inspection["blockers"]))

    provider_key = _resolve_provider_key(config.provider_key_env, env)
    profile = _PROVIDER_PROFILES[config.provider]
    allowed_hosts = tuple(str(h) for h in profile["hosts"])
    if config.provider is BYOKProvider.CUSTOM:
        parsed = urlsplit(config.endpoint)
        allowed_hosts = ((parsed.hostname or "").lower(),)

    _validate_https_url(config.endpoint, field_name="provider endpoint")
    parsed = urlsplit(config.endpoint)
    if (parsed.hostname or "").lower() not in allowed_hosts and config.provider is not BYOKProvider.CUSTOM:
        raise BYOKRunError("endpoint host not allowlisted at execution time")

    request = _build_request(config, plan, prompt_text, provider_key)

    opener = build_opener(NoRedirect, ProxyHandler({}))
    started = time.monotonic()
    http_status: int | None = None
    raw_bytes = b""
    error: str | None = None
    try:
        with opener.open(request, timeout=timeout_s) as response:
            http_status = getattr(response, "status", None) or response.getcode()
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_response_bytes:
                    raise BYOKRunError(
                        f"response exceeded max_response_bytes={max_response_bytes}"
                    )
                chunks.append(chunk)
            raw_bytes = b"".join(chunks)
    except BYOKRunError:
        raise
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        http_status = getattr(exc, "code", None)
    finally:
        elapsed = time.monotonic() - started

    output_text = ""
    output_sha256: str | None = None
    usage: dict[str, Any] = {}
    request_id: str | None = None
    if raw_bytes and not error:
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(payload, dict):
                output_text = _extract_output_text(config, payload)
                usage = _extract_usage(config, payload)
                request_id = (
                    payload.get("id")
                    or payload.get("response_id")
                    or (payload.get("response") or {}).get("id")
                )
        except (UnicodeDecodeError, json.JSONDecodeError):
            output_text = raw_bytes.decode("utf-8", errors="replace")
        output_sha256 = hashlib.sha256(output_text.encode("utf-8")).hexdigest()

    raw_saved = False
    if persist_output and output_text and output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(
                output_dir, f"byok_output_{int(time.time())}.txt"
            )
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(output_text)
            raw_saved = True
        except OSError:
            raw_saved = False

    outcome = "SUCCEEDED" if not error and http_status and 200 <= http_status < 300 else "FAILED"
    receipt = create_byok_receipt(
        plan,
        outcome=outcome,
        authorization_id=authorization_id,
        settlement_id=settlement_id,
        provider_request_id=request_id,
        output_sha256=output_sha256,
        provider_usage=usage,
        metadata={
            "http_status": http_status,
            "elapsed_s": round(elapsed, 3),
            "raw_response_saved_locally": raw_saved,
        },
        known_secrets=(provider_key, env.get(config.promptos_credential_env, "")),
    )

    serialized = json.dumps(receipt, ensure_ascii=False)
    if provider_key and provider_key in serialized:
        raise BYOKRunError("provider key leaked into run result")

    return BYOKRunResult(
        status="PASS" if outcome == "SUCCEEDED" else "FAILED",
        outcome=outcome,
        provider=config.provider.value,
        model=config.model,
        http_status=http_status,
        output_text=output_text,
        output_sha256=output_sha256,
        provider_usage=usage,
        provider_request_id=request_id,
        elapsed_s=elapsed,
        receipt=receipt,
        error=error,
        raw_response_saved=raw_saved,
    )

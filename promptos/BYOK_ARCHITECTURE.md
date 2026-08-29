# PromptOS BYOK Architecture

**Version:** 4.1.0-rc1  
**Status:** `CLIENT PREFLIGHT IMPLEMENTED — CONTROL PLANE AND LIVE PROVIDER EXECUTION PENDING`  
**Attribution:** RegenExcalibur — 1JGM / Justice Gray Maciocha

## Purpose

PromptOS BYOK (“bring your own key”) separates the customer's AI-provider account from RegenExcalibur's prompt-engineering and orchestration service.

The customer pays the model provider directly through their own provider account. RegenExcalibur charges for PromptOS compilation, routing, AutoDesign, AutoEngineer coordination, evaluation, governance, and related service value.

This avoids placing provider spend on RegenExcalibur by default and creates a clean commercial boundary:

```text
Customer device
├── provider key              → selected provider only
├── PromptOS access token     → PromptOS control plane only
├── compiled runtime prompt   → selected provider only
└── secret-free hashes/receipt→ PromptOS control plane
```

## Non-negotiable trust boundaries

1. **Provider credentials remain local.** The provider API key is resolved from an environment variable on the customer's computer. It must not be embedded in repository files, JSON configuration, command-line arguments, runtime prompts, logs, plans, receipts, or PromptOS control-plane requests.
2. **PromptOS credentials are separate.** `PROMPTOS_ACCESS_TOKEN` authorizes paid PromptOS capability. It must never be sent to a model provider.
3. **Control-plane location is explicit.** `PROMPTOS_CONTROL_PLANE_URL` identifies the future entitlement and metering service. Commercial mode fails closed when it is absent or non-HTTPS.
4. **The provider call is local.** The customer's device sends the compiled prompt directly to the configured allowlisted provider endpoint.
5. **PromptOS meters its own service.** PromptOS service units are not provider tokens, cryptocurrency, cash, stored value, or an assertion about provider billing.
6. **Receipts are secret-free.** Receipts may contain public provider request identifiers, hashes, usage counts, and state transitions, but never credentials or raw prompt content.
7. **Execution states remain distinct.** Planned, authorized, executed, settled, verified, and accepted are not interchangeable.

## Supported provider profiles

The RC1 preflight supports policy profiles for:

| Provider profile | Default key environment variable | Default API surface |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | Responses API |
| Anthropic | `ANTHROPIC_API_KEY` | Messages API |
| Google Gemini | `GEMINI_API_KEY` | `generateContent` API |
| Custom | `CUSTOM_PROVIDER_API_KEY` | Explicitly reviewed HTTPS endpoint |

The provider model identifier is always supplied by the customer. No model is silently selected, no provider key is collected, and no live provider request is performed by this release candidate.

## Commercial execution sequence

```text
1. Compile the customer's Foundry request locally.
2. Calculate a deterministic PromptOS service-unit quote.
3. Create an idempotent, secret-free authorization request.
4. PromptOS control plane validates account, plan, entitlements, limits, and payment state.
5. Control plane reserves the quoted service units.
6. Customer device resolves the provider key locally.
7. Customer device calls the allowlisted provider endpoint directly.
8. Local runtime hashes the output and creates a redacted receipt.
9. Control plane settles or cancels the reservation idempotently.
10. Customer receives separate PromptOS and provider billing records.
```

The checked-in client currently implements steps 1–3 and the secret-free receipt format. Steps 4–9 require the private control-plane and local execution adapters described in `BYOK_CONTROL_PLANE.md`.

## PromptOS service units

The public compiler can quote abstract `PROMPTOS_SERVICE_UNIT` quantities from the selected modules. The quote deliberately has:

```json
{
  "currency_value_assigned": false,
  "provider_model_usage_included": false
}
```

This prevents the repository from inventing prices or conflating provider model tokens with RegenExcalibur's service value. Actual CAD/USD prices, subscriptions, taxes, refunds, expiry, and customer rights remain owner-controlled commercial decisions.

## Configuration model

Configuration contains environment-variable names, never secret values:

```json
{
  "provider": "openai",
  "model": "SET_PROVIDER_MODEL_ID",
  "endpoint": "https://api.openai.com/v1/responses",
  "provider_key_env": "OPENAI_API_KEY",
  "promptos_credential_env": "PROMPTOS_ACCESS_TOKEN",
  "control_plane_url_env": "PROMPTOS_CONTROL_PLANE_URL",
  "require_promptos_credential": true,
  "require_control_plane_authorization": true,
  "allow_custom_endpoint": false,
  "execution_mode": "LOCAL_DIRECT"
}
```

Literal fields such as `api_key`, `secret`, `password`, and `access_token` are rejected.

## Endpoint policy

Official provider profiles are restricted to their allowlisted HTTPS hosts. Authentication-header overrides are rejected for official profiles. Custom endpoints require an explicit review flag and remain the customer's responsibility.

Provider credentials in URL query parameters, embedded URL usernames/passwords, HTTP endpoints, and URL fragments are rejected.

## Threat model

The current implementation directly addresses:

- accidental credential commits;
- provider keys copied into configuration files;
- provider keys included in PromptOS authorization bodies;
- PromptOS access tokens sent to providers;
- malicious provider-host substitution for official profiles;
- secret-bearing URL queries;
- credential leakage through plans and receipts;
- duplicate billing intent through missing idempotency keys;
- false claims that local preflight equals paid authorization or provider execution.

It does **not** prove protection against a compromised customer device, malicious operating-system process, hostile shell history, keylogger, compromised Python runtime, compromised provider, compromised future control plane, or every prompt-injection technique.

## Platform boundary

The local-direct mode is intended for controlled command-line, desktop, server, or developer environments. Provider keys must not be embedded in distributable browser JavaScript or mobile application packages.

A browser or mobile product requires a different architecture in which provider access is mediated by a secure backend or by a provider-supported user authorization mechanism. That mode is not implemented here.

## Completion states

| State | Meaning |
|---|---|
| `CLIENT_PREFLIGHT_IMPLEMENTED_CONTROL_PLANE_PENDING` | Configuration, environment, quote, authorization-body, and receipt contracts exist. |
| `CONTROL_PLANE_IMPLEMENTED_PROVIDER_EXECUTION_PENDING` | Paid authorization and settlement work, but local provider adapters are incomplete. |
| `END_TO_END_IMPLEMENTED_EVALUATION_PENDING` | Authorization, local provider execution, settlement, and receipts operate together. |
| `VERIFIED_RELEASE_CANDIDATE` | Security, billing, provider, failure, and regression tests pass at an immutable revision. |
| `RELEASED` | Owner-approved commercial terms, deployment, monitoring, support, and release evidence exist. |

## Present terminal state

**CLIENT PREFLIGHT IMPLEMENTED — CONTROL PLANE AND LIVE PROVIDER EXECUTION PENDING.**

# PromptOS BYOK Control-Plane Contract

**Status:** implementation specification; no live billing endpoint is claimed.

## Responsibility boundary

The private PromptOS control plane will own:

- account authentication;
- plan and entitlement checks;
- subscription/payment status;
- service-unit quotes and reservations;
- idempotent authorization;
- idempotent settlement and cancellation;
- account-level rate and spend limits;
- abuse controls;
- append-only commercial ledger entries;
- auditable receipts;
- refunds and dispute workflow;
- administrator review and revocation.

It must never receive the customer's model-provider API key.

The local client will own:

- loading the provider key from the customer's environment;
- compiling or loading the PromptOS runtime prompt;
- calling the selected provider directly;
- retaining raw provider responses locally;
- producing a redacted result receipt;
- transmitting only permitted hashes, counts, identifiers, and settlement metadata.

## Credential domains

| Credential | Recipient | Forbidden recipients |
|---|---|---|
| Provider key | Configured provider endpoint | PromptOS control plane, logs, repository, receipts |
| PromptOS access token | PromptOS control plane | Model provider, runtime prompt, receipt |
| Payment credentials | Payment processor-hosted surface | PromptOS source, provider, GitHub |
| Internal signing/ledger secrets | Private control-plane secret store | Client, repository, provider |

## Required API operations

The normative draft is in `specs/byok-control-plane.openapi.yaml`.

### `POST /v1/byok/authorize`

Purpose: validate the account and reserve PromptOS service units before provider execution.

Required request properties:

- idempotency key;
- provider and model identifiers;
- source SHA-256;
- runtime-prompt SHA-256;
- requested service-unit quote;
- execution mode;
- explicit negative assertions that provider key, source text, and runtime prompt are absent.

The control plane must reject:

- inactive or revoked accounts;
- invalid or expired access tokens;
- unsupported operations or modules;
- quote mismatch;
- exceeded limits;
- delinquent payment state;
- duplicate idempotency keys with conflicting bodies;
- requests containing provider credentials or raw prompt material.

### `POST /v1/byok/settle`

Purpose: capture the reserved PromptOS service units after local provider execution.

Settlement must be idempotent and bind:

- authorization identifier;
- receipt SHA-256;
- runtime-prompt SHA-256;
- outcome;
- provider request identifier when available;
- output SHA-256 when available;
- allowed provider usage counts;
- final service units.

Provider model costs remain between the customer and provider.

### `POST /v1/byok/cancel`

Purpose: release a reservation when execution is cancelled or fails before a chargeable PromptOS outcome is reached.

Cancellation must preserve a ledger record and must not delete the original authorization evidence.

## Minimum data model

```text
accounts
- account_id
- status
- created_at
- payment_customer_reference

access_tokens
- token_id
- account_id
- token_hash
- scopes
- expires_at
- revoked_at

entitlements
- account_id
- plan_code
- enabled_operations
- enabled_modules
- rate_limits
- effective_from
- effective_until

reservations
- authorization_id
- account_id
- idempotency_key
- request_body_sha256
- quoted_units
- status
- expires_at

ledger_entries
- entry_id
- account_id
- authorization_id
- event_type
- units
- canonical_event_sha256
- created_at

receipts
- receipt_id
- authorization_id
- receipt_sha256
- settlement_id
- outcome
- created_at

webhook_events
- processor_event_id
- event_type
- payload_sha256
- processing_state
- received_at
```

Commercial balances must derive from append-only ledger events, not from an untraceable mutable number.

## State machine

```text
REQUESTED
  ├─→ BLOCKED
  └─→ AUTHORIZED_RESERVED
          ├─→ CANCELLED_RELEASED
          ├─→ EXPIRED_RELEASED
          └─→ SETTLED_CAPTURED
                  ├─→ REFUND_PENDING
                  └─→ REFUNDED
```

A retry with the same idempotency key and identical body must return the original result. A retry with the same idempotency key and different body must fail.

## Privacy and minimization

The control plane should receive only what it needs to authorize and account for PromptOS service. By default it should not receive:

- provider API keys;
- raw prompts;
- source documents;
- raw model outputs;
- unrelated personal information;
- customer provider invoices;
- full payment-card details.

Hashes are identifiers, not magical anonymization. Sensitive or guessable source text may still require contractual and privacy controls even when represented by a hash.

## Security requirements

- HTTPS only.
- Hashed PromptOS access tokens at rest.
- Short-lived scoped tokens where practical.
- Constant-time credential comparison.
- Rate limits by account, token, IP risk signal, and operation.
- Idempotency on every financial mutation.
- Append-only ledger and immutable event identifiers.
- Payment webhook signature verification.
- No provider-key fields accepted at any endpoint.
- Structured logging with secret redaction.
- Alerting for repeated authorization failures and settlement anomalies.
- Administrative revocation and incident-response runbook.
- Backup, restoration, retention, and deletion policy.
- Independent security review before public commercial activation.

## Pricing boundary

The repository quotes abstract PromptOS service units. The private control plane maps plans and units to commercial terms approved by the owner.

Possible commercial forms:

- fixed monthly BYOK subscription with included operations;
- subscription plus service-unit overages;
- prepaid PromptOS service-unit packs;
- fixed-price AutoDesign/AutoEngineer packages;
- enterprise/OEM licence plus support;
- manual invoice for high-value engagements.

Service units must not be promoted as cryptocurrency, investments, transferable financial instruments, or provider model tokens.

## Required production evidence

Before paid activation, retain evidence for:

1. authentication and revocation tests;
2. duplicate authorization/settlement tests;
3. reservation expiry and cancellation tests;
4. payment webhook replay/tamper tests;
5. provider-key non-collection tests;
6. logging redaction tests;
7. rate-limit and abuse tests;
8. ledger reconciliation tests;
9. refund tests;
10. backup and restore tests;
11. privacy and terms review;
12. exact-deployment revision and configuration receipt.

## Current terminal state

**CONTROL-PLANE CONTRACT COMPLETE — PRIVATE IMPLEMENTATION AND PAYMENT ACTIVATION PENDING.**

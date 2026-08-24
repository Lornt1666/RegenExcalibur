# ProofGrid v3.0 — Authoritative IFC Model Inventory Basis

## Status

**Engine scaffold / preflight only until a user-authorized native `.ifc` is supplied.**

The v3.0 production verdict is:

`MODEL_INVENTORY_BASIS_CLOSED_FOR_POLICY`

That verdict is unreachable from the synthetic CI fixtures in this branch.

Synthetic tests can emit only:

`V30_ENGINE_PREFLIGHT_VERIFIABLE`

## Purpose

v3.0 defines the first ProofGrid gate that can establish model-inventory completeness for one exact IFC revision under one exact immutable policy.

It does not establish:

- complete-building LCA;
- environmental evidence coverage;
- scientific validity;
- professional review;
- regulator acceptance;
- certification.

## Immutable inventory policy

`policies/inventory-policy-v30.json`

Exact policy SHA-256:

`67b1da24c5ec579942d2d21919dcc688f28ee0bf1057d18f93aba2bf9aab500b`

The engine rejects any policy byte drift.

## Enumeration basis

The policy enumerates `IfcProduct` including subtypes.

Each enumerated product is classified exactly once as:

- `EVIDENCE_REQUIRED`
- `EVIDENCE_NOT_APPLICABLE`
- `OUT_OF_DECLARED_EVIDENCE_SCOPE`

No enumerated object may silently disappear.

The initial environmental evidence policy classifies:

- `IfcElement` as `EVIDENCE_REQUIRED`;
- `IfcOpeningElement` as `EVIDENCE_NOT_APPLICABLE` with reason `OPENING_VOID_FEATURE`;
- non-element `IfcProduct` objects as `OUT_OF_DECLARED_EVIDENCE_SCOPE` with reason `NON_ELEMENT_PRODUCT`.

## Captured inventory evidence

Each entry records:

- exact IFC source SHA-256;
- STEP ID;
- non-empty GlobalId;
- IFC type;
- containment and decomposition parents;
- material association relationship identities;
- declared quantity-set and quantity STEP identities;
- project/explicit unit identities;
- exact STEP lexical quantity tokens for supported declared quantity types;
- parser numeric values as non-authoritative consistency evidence;
- one policy state and required reason where applicable.

## Exact numeric authority

For supported `IfcQuantity*` entities:

`STEP lexical token = evidence authority`

`IfcOpenShell numeric value = consistency evidence only`

A lexical/parser mismatch fails closed.

## Source authorization

A real production closure requires a separate authorization record with:

- `source_classification = USER_AUTHORIZED_REAL_IFC`
- `user_authorized = true`
- `synthetic = false`
- `reconstructed = false`
- explicit authorization reference.

Synthetic fixtures are allowed only with `--preflight`, and cannot produce the production verdict.

## Resource/security policy

The engine enforces:

- native `.ifc` input only;
- 100 MiB source-file ceiling;
- entity/product budgets;
- per-product material/quantity budgets;
- STEP-record size budget;
- duplicate STEP rejection;
- duplicate non-empty GlobalId rejection;
- local parsing only;
- Python-level network connection denial during IFC parsing;
- supported IFC schema-family checks.

## CI preflight

The pull-request workflow runs two independent synthetic replicas to verify engine determinism and mandatory negative behavior.

That preflight is **not** Issue #98 acceptance.

Issue #98 remains open until an actual user-authorized native IFC is available to two clean hosted runners and the resulting production evidence is byte-identical.

## Real-source blocker

As of this branch, no native `.ifc` exists in the current ChatGPT conversation or persistent file Library.

OpenBIM-derived graphs and reconstructed/synthetic IFCs are explicitly prohibited from satisfying the production gate.

**Attribution:** RegenExcalibur / 1JGM

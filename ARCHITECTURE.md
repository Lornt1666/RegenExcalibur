# ProofGrid / RX Evidence Fabric Architecture v0.1

## Purpose

ProofGrid is RegenExcalibur's first open reference implementation for turning built-environment data into traceable, machine-readable evidence.

The first slice is intentionally small:

`project + materials -> deterministic calculation -> evidence bundle -> integrity receipt`

It does **not** replace architects, engineers, code officials, auditors, lifecycle-assessment practitioners, or certification bodies.

## Layers

1. **Constitution** — safety, truth, authority, evidence, privacy, interoperability.
2. **Adapters** — IFC/BIM, LCA/EPD, telemetry, code and other external formats.
3. **RX Evidence Protocol (RXEP)** — claims, measurements, provenance, review state, integrity metadata.
4. **Knowledge graph** — subject/claim/source relationships.
5. **ForgeOS orchestration** — future workflows, approvals, agents, policy gates.
6. **Applications** — blueprint intelligence, carbon analysis, retrofit, infrastructure, environmental monitoring.
7. **Commercial services** — optional hosting, enterprise integrations, managed workflows, support.

## Cloud-neutral rule

The protocol and reference verifier must run locally without a paid cloud dependency. Cloud providers are adapters and deployment targets, not protocol requirements.

## Deterministic-core rule

Numeric evidence used for verification must be produced by deterministic code or an explicitly declared numerical method. AI may assist with extraction, mapping, and explanation, but inferred outputs must not be silently presented as deterministic facts.

## Genesis acceptance criteria

The v0.1 genesis slice is acceptable when:

- a fictional Alberta sample project can be verified locally;
- the same declared inputs and calculation version produce the same numerical result;
- source files are SHA-256 hashed;
- evidence output states its methodology and limitations;
- output distinguishes `VERIFIABLE` from `CERTIFIED`;
- automated tests cover calculation and artifact generation;
- CI can execute without secrets or billable infrastructure.

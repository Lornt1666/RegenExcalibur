# RegenExcalibur ProofGrid / RX Evidence Fabric — Production Architecture v1

**Status:** architecture target; documentation only.  
**Baseline:** accepted ProofGrid v2.12 bounded synthetic inventory basis, exact head `7ee4c3785a1e8bd3717c4bbd8c0ab5437c278c5a`.  
**Attribution:** RegenExcalibur / 1JGM. Material AI assistance must be disclosed where appropriate.  

## 1. Mission and non-negotiable doctrine

ProofGrid is the deterministic evidence kernel for RegenExcalibur: a cloud-neutral, local-first infrastructure layer that turns source material, IFC/model data, environmental declarations, explicit human-reviewed mappings, calculations, and scope definitions into machine-verifiable evidence without promoting evidence beyond what has actually been proven.

Invariant doctrine:

1. Truth before promotion.
2. Evidence before theory.
3. Safety before autonomy.
4. Credit/provenance before publication.
5. Human authority before consequential real-world control.
6. Public availability is not equivalent to reuse authority.
7. Software reproduction is not scientific validation, professional review, regulatory acceptance, or certification.
8. Missing evidence is never silently converted to zero.
9. Binary floating point is never authority for exact environmental arithmetic when source lexical/Decimal authority exists.
10. Every promotion of scope, review state, rights state, or certification state must be explicit and independently verifiable.

## 2. Current proven nucleus

The accepted synthetic chain now proves, in a bounded synthetic test scope:

- exact source hashing and deterministic receipts;
- rights-aware environmental source admission;
- ILCD+EPD conformance routing with bounded claims;
- explicit IFC-to-declaration mapping without fuzzy-name authority;
- exact STEP lexical quantity preservation and Decimal authority;
- exact environmental contribution calculation;
- RXEP `CALCULATED` evidence binding;
- anti-double-count contribution-set membership;
- exact Decimal aggregation;
- declared inventory gap detection and remediation;
- predecessor→successor source revision continuity;
- 3/3 evidence coverage for an explicit three-entry synthetic inventory;
- closure of an immutable bounded synthetic inventory basis.

This is a strong evidence-kernel proof. It is **not** yet proof of a complete real IFC model inventory, complete building LCA, scientific validity, professional review, regulatory acceptance, or certification.

## 3. Final system decomposition

Production ProofGrid is divided into ten trust-separated layers.

### L0 — Content-addressed Evidence Kernel

Responsibilities:

- SHA-256 content and file identities;
- canonical UTF-8 JSON representation;
- exact Decimal canonicalization;
- immutable receipt generation;
- deterministic state transitions;
- append-only evidence ledger;
- signature/attestation interfaces without treating signatures as truth.

Rule: every higher layer may consume L0 identities; no higher layer may rewrite accepted evidence in place.

### L1 — Source Intake and Rights Gate

Responsibilities:

- exact source-byte admission;
- source type/version detection;
- authorization/terms manifest;
- storage, transformation, commercial-use, and redistribution permissions;
- expiry/approval checking;
- content/terms hash binding;
- sandboxed parser routing.

States:

`DISCOVERED → RIGHTS_UNRESOLVED → RIGHTS_AUTHORIZED → AWAITING_CONFORMANCE → CONFORMANT_FOR_BOUNDED_PURPOSE → ADMITTED_FOR_NORMALIZATION`

Failure is terminal for the attempted admission unless a new rights/conformance receipt is created.

### L2 — Authoritative Model Inventory Engine

This is the next production-critical subsystem.

Input is **one exact model revision** plus **one immutable inventory policy manifest**.

For IFC, the engine must:

1. hash exact IFC bytes;
2. identify schema/version and parser version;
3. enumerate model objects under an explicit policy rather than silently selecting convenient elements;
4. preserve STEP IDs, GlobalIds, IFC type, containment/decomposition path, material-association identities, declared quantity identities, units, and exact STEP lexical quantities where applicable;
5. classify each enumerated object into exactly one evidence-policy state:
   - `EVIDENCE_REQUIRED`,
   - `EVIDENCE_NOT_APPLICABLE`,
   - `OUT_OF_DECLARED_EVIDENCE_SCOPE`;
6. preserve excluded/not-applicable objects in the inventory ledger with explicit reasons;
7. emit an immutable `ModelInventoryBasis` and receipt.

No object may disappear between enumeration and scope classification without a receipt-level error.

### L3 — Environmental Declaration / Source Evidence Engine

Responsibilities:

- rights-aware declaration ingestion;
- deterministic version/conformance routing;
- exact declaration/product/reference-flow identity closure;
- exact declared indicator/module/scenario row extraction;
- source-declared units and reference basis preservation;
- no scientific-validity inference from syntactic/profile conformance.

A declaration may be syntactically conformant yet scientifically unsuitable; those are separate states.

### L4 — Explicit Mapping and Quantity Authority Engine

Responsibilities:

- bind one exact model element/material/quantity identity to one exact environmental product/reference-flow identity;
- require explicit human-reviewed mapping artifacts where semantic judgment is involved;
- forbid fuzzy names as authority;
- bind exact quantity lexical tokens and canonical Decimal values;
- record any unit conversion as an explicit reviewed transformation; default is no implicit conversion.

Mapping state:

`UNMAPPED → MAPPING_PROPOSED → REVIEWED_MAPPING_DECISION → MAPPED_FOR_CALCULATION`

### L5 — Deterministic Calculation Engine

Arithmetic authority:

- canonical Decimal source quantity;
- exact reference basis;
- exact source-declared environmental row;
- explicit formula version.

Required properties:

- no binary-float authority;
- no hidden rounding;
- no inferred scenario;
- no missing module treated as zero;
- deterministic member/order-independent aggregate behavior where mathematically applicable.

Outputs remain `CALCULATED` until human review occurs.

### L6 — Contribution Set, Aggregation, and Coverage Engine

Three distinct concepts must remain separate:

1. **membership** — which exact contributions are admitted;
2. **aggregation** — arithmetic over admitted compatible members;
3. **coverage** — whether a declared inventory/scope has evidence for all required members.

Anti-double-count identity must bind source/model lineage, element identity, mapping identity, declaration identity, indicator/module/scenario, and exact value—not display labels or wrapper IDs.

A total is always labeled by its scope:

`ADMITTED_SET_MEMBERS_ONLY`, `BOUNDED_MANIFEST`, or another explicit scope identifier.

### L7 — RXEP / Evidence Fabric

RXEP is the portable evidence-envelope protocol.

Required envelope properties:

- exact subject and claim identity;
- exact Decimal authority where applicable;
- non-authoritative display numeric field clearly marked;
- source/receipt identities;
- method/version;
- limitations;
- review state;
- evidence-scope/completeness state;
- software-reproduction state;
- scientific/professional/regulatory/certification states as independent dimensions.

Review states:

`CLAIMED → CALCULATED → REVIEWED → INDEPENDENTLY_VERIFIED`

Software reproduction never automatically advances this review state.

### L8 — Human Authority and Governance Plane

Human decisions are first-class signed/attributed artifacts.

Governed actions include:

- mapping approval;
- source-rights approval;
- scope-policy approval;
- scientific suitability review;
- professional engineering/architectural review where legally required;
- regulatory/certification claims;
- production release;
- external publication/export.

No AI agent receives authority to invent credentials, accept external terms, certify results, or make legally consequential professional claims.

### L9 — ForgeOS Orchestration Plane

ForgeOS is above the Evidence Kernel. It coordinates work; it does not redefine truth.

Responsibilities:

- job DAGs;
- retries and idempotency;
- connector adapters;
- human approval queues;
- scheduling;
- policy evaluation;
- evidence collection;
- rollback/reconciliation;
- presentation to non-technical users.

ForgeOS may request an evidence transition, but the deterministic verifier decides whether the transition is valid.

## 4. Canonical production state model

Every material operation emits a new immutable state object.

```text
SOURCE
  DISCOVERED
  → RIGHTS_AUTHORIZED
  → CONFORMANT_FOR_BOUNDED_PURPOSE
  → ADMITTED_FOR_NORMALIZATION

MODEL
  MODEL_RECEIVED
  → MODEL_BYTES_PINNED
  → INVENTORY_POLICY_PINNED
  → INVENTORY_ENUMERATED
  → INVENTORY_CLASSIFIED
  → MODEL_INVENTORY_BASIS_CLOSED

ELEMENT / CONTRIBUTION
  INVENTORIED
  → QUANTITY_EVIDENCED
  → MAPPING_REVIEWED
  → CALCULATED
  → RXEP_BOUND
  → SET_ADMITTED

SCOPE
  SCOPE_DECLARED
  → MEMBERSHIP_CLOSED
  → EVIDENCE_COVERAGE_EVALUATED
  → AGGREGATED
  → REVIEWED

EXTERNAL AUTHORITY
  SCIENTIFICALLY_REVIEWED        (independent dimension)
  PROFESSIONALLY_REVIEWED        (independent dimension)
  REGULATOR_ACCEPTED             (independent dimension)
  CERTIFIED                      (independent dimension)
```

No transition may be inferred merely because a later-looking field exists.

## 5. Storage model

Local-first default:

- immutable artifacts: filesystem/content-addressed object directory;
- structured metadata: SQLite for single-user/local development;
- production multi-user profile: PostgreSQL;
- optional S3-compatible object storage adapter;
- append-only audit/event ledger;
- no mandatory vendor-specific cloud service.

Core tables/collections:

- `source_objects`
- `rights_manifests`
- `conformance_receipts`
- `model_revisions`
- `inventory_policies`
- `inventory_entries`
- `environmental_declarations`
- `mapping_decisions`
- `quantity_evidence`
- `calculation_records`
- `rxep_envelopes`
- `contribution_sets`
- `scope_manifests`
- `coverage_receipts`
- `review_decisions`
- `release_receipts`
- `audit_events`

Mutations create successor records; accepted evidence is never overwritten.

## 6. API boundary

Reference service: Python 3.11+ / FastAPI / Pydantic v2, with deterministic reference functions remaining callable without HTTP.

Minimum API:

```text
POST /v1/sources/admit
POST /v1/models/admit
POST /v1/models/{model_id}/inventory
POST /v1/declarations/admit
POST /v1/mappings
POST /v1/calculations
POST /v1/contribution-sets
POST /v1/scopes
POST /v1/scopes/{scope_id}/coverage
POST /v1/rxep
POST /v1/reviews
GET  /v1/receipts/{sha256}
GET  /v1/evidence/{sha256}
GET  /health
GET  /ready
```

Every write endpoint requires:

- idempotency key;
- caller identity;
- requested transition;
- exact parent digests;
- policy version;
- explicit error receipt on fail-closed rejection.

## 7. Security architecture

Threats explicitly handled:

- malicious IFC/XML;
- XML external entities and remote schema resolution;
- ZIP/path traversal;
- decompression bombs;
- parser resource exhaustion;
- source/receipt substitution;
- forged self-consistent receipts;
- dependency/supply-chain compromise;
- secret leakage in logs/artifacts;
- authorization confusion;
- evidence-state overpromotion;
- duplicate/double-count contributions;
- rights/licensing violations.

Controls:

- parser sandbox/resource budgets;
- no network resolution during deterministic validation unless an explicitly admitted fetch stage produced pinned bytes;
- allowlisted file roots;
- path canonicalization;
- size/entity/depth limits;
- pinned dependencies with hashes where practical;
- SBOM and dependency audit in release CI;
- structured redaction;
- least-privilege service identities;
- tenant isolation in multi-user mode;
- cryptographic content binding at every trust transition.

## 8. Observability

OpenTelemetry-compatible traces/metrics/logs are optional adapters, not truth authorities.

Required operational telemetry:

- admission counts and rejection reasons;
- parser duration/resource usage;
- inventory counts by policy state;
- mapping approval queue age;
- calculation/coverage latency;
- deterministic reproduction mismatch count;
- receipt verification failures;
- rights-expiry warnings;
- release-gate state.

Never log raw confidential source bytes, secrets, or unnecessary personal data.

## 9. Release and CI policy

Repository discipline remains:

1. branch from an exact accepted SHA;
2. isolated/stacked feature branch;
3. draft PR;
4. exact-head hosted CI;
5. retained bounded evidence artifact;
6. explicit acceptance receipt;
7. merge only under separate owner authorization.

Production release requires all of:

```text
exact_head_verified
and dependency_lock_verified
and schema_migrations_verified
and evidence_contracts_verified
and rights_policy_verified
and security_scan_no_blocking_findings
and secrets_scan_clean
and backup_restore_rehearsed
and rollback_rehearsed
and observability_healthy
and human_release_approval_present
```

A signed binary/container proves build provenance, not correctness or scientific truth.

## 10. Deployment profiles

### Profile A — Local Evidence Workbench

- one workstation;
- SQLite + local object store;
- no external network required after source acquisition;
- best for zero-cost development and sensitive evidence work.

### Profile B — Team / Private Server

- containerized API + worker;
- PostgreSQL;
- S3-compatible object store or filesystem;
- reverse proxy/TLS;
- OIDC/RBAC;
- audit retention and encrypted backups.

### Profile C — Cloud-neutral Production

Same containers/contracts as Profile B with provider adapters for database, object storage, secrets, queues, and telemetry. Provider-specific features must never become canonical evidence requirements.

## 11. Interoperability strategy

Core protocol remains open and adapter-driven.

Priority adapters:

- IFC / building model inventory;
- ILCD+EPD / environmental declarations;
- RXEP evidence envelopes;
- optional Brick/Haystack for operational building semantics;
- OpenTelemetry for runtime observability;
- OSCAL-compatible control/evidence exports where useful for security/compliance evidence.

Adapters translate into canonical ProofGrid records; they cannot bypass kernel validation.

## 12. Production-readiness ladder

### P0 — Synthetic deterministic proof

Status: substantially achieved through accepted v2.12 bounded synthetic evidence.

### P1 — Real model inventory basis

Required next milestone:

- user-authorized real IFC file;
- exact bytes retained/hash-pinned;
- immutable inventory policy;
- complete policy-based enumeration;
- zero silent drops;
- two independent clean-environment reproductions of inventory bytes/counts;
- explicit `EVIDENCE_REQUIRED / NOT_APPLICABLE / OUT_OF_SCOPE` classification.

### P2 — Real rights-authorized environmental-source lane

- lawful source access;
- terms/rights captured;
- exact source bytes;
- exact version/profile validation;
- no redistribution beyond permissions.

### P3 — Real model-to-environmental mapping pilot

- bounded set of real elements;
- qualified human mapping review;
- exact quantities;
- exact source-declared rows;
- no unsupported scientific suitability claim.

### P4 — Reviewed bounded real-project result

- explicit scope manifest;
- inventory coverage receipt;
- qualified domain review;
- limitations and exclusions published;
- no whole-building claim unless basis actually proves it.

### P5 — Security/privacy/operational production gate

- auth/RBAC;
- backup/restore;
- incident response;
- load/performance testing;
- penetration/security assessment;
- retention/deletion policy;
- signed release artifacts;
- external rights/privacy review where appropriate.

### P6 — External assurance

Only external competent authorities may establish certification, accreditation, regulated professional approval, or regulator acceptance.

## 13. Immediate next implementation gate

**ProofGrid v3.0 — authoritative real IFC model-inventory basis.**

Acceptance contract:

1. one user-authorized IFC revision is the sole input model;
2. exact input SHA-256 is frozen;
3. an immutable `inventory-policy.json` defines enumeration and classification rules;
4. every policy-enumerated object receives one canonical inventory entry;
5. no duplicate `(source_sha256, STEP_ID)` or duplicate non-empty GlobalId is silently accepted;
6. exact source type, STEP ID, GlobalId, decomposition/containment identity, material-association IDs, and quantity IDs are preserved when present;
7. all exclusions/not-applicable classifications carry explicit reason codes;
8. inventory count, identity set, canonical record, and receipt reproduce byte-for-byte on two independent hosted runners;
9. parser/network/path/resource attacks fail closed;
10. output may say `MODEL_INVENTORY_BASIS_CLOSED_FOR_POLICY`, but may **not** say whole-building LCA complete, scientifically valid, professionally reviewed, or certified.

## 14. Definition of architectural completion

The architecture is considered complete when every subsystem has:

- a canonical input/output contract;
- a deterministic verifier;
- explicit authority boundaries;
- fail-closed negative tests;
- an immutable receipt;
- human-review points where semantic/legal/professional judgment is required;
- cloud-neutral deployment behavior;
- observability and recovery requirements;
- no implicit promotion of truth, rights, review, scope, or certification.

The implementation is considered production-ready only when the relevant P1–P5 gates have been proven on the intended real deployment and P6 claims are made only when actually granted by external authority.

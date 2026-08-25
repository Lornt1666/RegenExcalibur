# ProofGrid v3.0 — Real IFC Source Handoff Contract

## Purpose

This contract governs the transition from the validated v3.0 engine preflight to the real-source production gate in Issue #98.

It exists to prevent three failures:

1. publishing a private/proprietary model merely to make CI run;
2. replacing the user's native IFC with a reconstructed or derived substitute;
3. allowing different runners to validate different source bytes.

## Default source-privacy rule

A user-supplied IFC is **private by default**.

The public `Lornt1666/RegenExcalibur` repository must not receive the source IFC bytes unless the user separately and explicitly authorizes public publication of that exact file.

Repository source code, policy, schemas, receipts, and hashes may be public while the model itself remains private.

## Required source sequence

### H0 — Native source supplied

The user supplies one native `.ifc` file.

Derived OpenBIM graphs, PDFs, screenshots, IFC-like JSON, reconstructed models, synthetic IFCs, and regenerated IFCs do not satisfy this step.

### H1 — Local byte freeze

Before semantic processing:

- record exact filename;
- record exact byte length;
- compute SHA-256 of the original file bytes;
- record source classification `USER_AUTHORIZED_REAL_IFC`;
- create a separate source-authorization record conforming to `schemas/model-source-authorization-v30.schema.json`;
- verify `synthetic=false` and `reconstructed=false`.

Any subsequent source-byte change creates a different model revision and requires a new admission chain.

### H2 — User authority record

The authorization record must state:

- exact purpose: `ProofGrid v3.0 authoritative model inventory basis`;
- `user_authorized=true`;
- `source_classification=USER_AUTHORIZED_REAL_IFC`;
- `synthetic=false`;
- `reconstructed=false`;
- an explicit authorization reference identifying the handoff event/source.

Authorization to **analyze** the IFC does not automatically authorize publication, redistribution, training use, or indefinite retention.

## Hosted two-runner delivery

Issue #98 requires two clean hosted runners to consume the **same exact source bytes**.

Accepted transport characteristics:

- private/access-controlled delivery;
- source SHA-256 verified by each runner before parsing;
- immutable object/version during the run;
- no automatic network discovery or alternative-source fallback;
- no conversion/re-export before the source hash is verified;
- both runners independently verify the same policy SHA-256;
- transport logs/metadata must not become evidence authority for model content.

### Public repository transport

Public-repository storage is prohibited by default.

It is permitted only after a separate explicit user instruction authorizes publication of the exact IFC bytes. Permission to run ProofGrid is not publication permission.

### Private staged transport

Preferred for proprietary/project models:

1. place the exact native IFC in a private staged object/artifact location;
2. pin exact source SHA-256 and object/version identifier;
3. grant read-only access only to the bounded validation runners;
4. each runner downloads the object and rejects it unless SHA-256 matches the locally frozen source identity;
5. delete or revoke staged access after the evidence window unless retention was separately authorized.

The current ChatGPT/GitHub connector surface does not itself establish such a private binary-artifact channel. Therefore the real hosted gate remains blocked until a private delivery mechanism is available or the user explicitly authorizes another transport.

## Runner invariants

Each production runner must receive:

- identical exact IFC bytes;
- identical `inventory-policy-v30.json` bytes;
- identical source-authorization bytes;
- identical dependency lock;
- identical inventory-engine revision.

Before parsing, each runner must verify:

```text
source_sha256 == admitted_source_sha256
policy_sha256 == 67b1da24c5ec579942d2d21919dcc688f28ee0bf1057d18f93aba2bf9aab500b
source_classification == USER_AUTHORIZED_REAL_IFC
synthetic == false
reconstructed == false
```

## Required independent outputs

Both clean runners must independently emit byte-identical:

- `model-admission-receipt.json`;
- `model-inventory-basis.json`;
- `model-inventory-basis-receipt.json`;
- inventory count;
- canonical inventory identity-set SHA-256.

The final production comparison receipt must bind both runner outputs and record `independent_runner_count=2` and `byte_identical=true`.

## Mandatory source/privacy negatives

Reject:

- source SHA mismatch;
- changed source object/version;
- derived or reconstructed substitute;
- synthetic source promotion;
- missing user authorization;
- authorization-purpose mismatch;
- unauthorized public-repository publication;
- source URL/object fallback to different bytes;
- policy drift;
- runner A / runner B source mismatch.

## Evidence-state boundary

Successful real-source inventory closure means only:

`MODEL_INVENTORY_BASIS_CLOSED_FOR_POLICY`

It does not establish:

- complete-building LCA;
- environmental evidence coverage;
- scientific validity;
- professional review;
- regulator acceptance;
- certification.

## Current state

As of the v3.0 preflight branch, no user-authorized native `.ifc` exists in the current conversation or persistent Library.

Therefore:

`IMPLEMENTATION_READY_REAL_SOURCE_BLOCKED`

Issue #98 must remain open and PR #100 must remain draft/unmerged until this contract is satisfied with real source bytes.

**Attribution:** RegenExcalibur / 1JGM

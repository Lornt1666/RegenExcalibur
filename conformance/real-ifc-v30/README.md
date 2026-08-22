# ProofGrid v3.0 — authoritative real IFC model-inventory basis

**Tracks:** #98  
**Architecture:** `docs/architecture/PROOFGRID_PRODUCTION_ARCHITECTURE_V1.md`  
**Attribution:** RegenExcalibur / 1JGM

## Current state

The v3.0 verifier, policy, schemas, and synthetic/mechanical preflight suite exist. **No user-authorized native `.ifc` file is currently present in the ChatGPT conversation or persistent file library.** Therefore the real-source acceptance gate is intentionally not satisfied and Issue #98 must remain open.

Synthetic fixtures may prove parser/enumerator mechanics only. They emit:

- `MODEL_BYTES_PINNED_TEST_ONLY`;
- `MODEL_INVENTORY_BASIS_TEST_ONLY`;
- `acceptance_eligible=false`.

They cannot satisfy v3.0 acceptance.

## Exact real-input contract

A real acceptance attempt requires both:

1. exact user-authorized IFC bytes;
2. a `ProofGridRealIFCAuthorization` manifest whose `source_sha256` equals those exact bytes.

The repository-hosted real gate expects, **only when the user explicitly authorizes placing the model in this repository**:

```text
conformance/real-ifc-v30/authorized-real-model.ifc
conformance/real-ifc-v30/source-authorization.json
```

If the IFC is confidential or should not be committed, do not use that repository path. The same deterministic engine should instead be fed the bytes through an approved private artifact/intake channel, while preserving the exact source and authorization SHA-256 values and two-runner reproduction requirement.

## Inventory policy

`inventory-policy.json` is immutable input evidence. It enumerates:

- `IfcProject`;
- `IfcSite`;
- `IfcBuilding`;
- `IfcBuildingStorey`;
- `IfcSpace`;
- every `IfcElement` subtype.

Every unique policy-enumerated STEP object must be classified exactly once as:

- `EVIDENCE_REQUIRED`;
- `EVIDENCE_NOT_APPLICABLE`;
- `OUT_OF_DECLARED_EVIDENCE_SCOPE`.

The current policy marks context/spatial objects and `IfcOpeningElement` as not applicable; other `IfcElement` subtypes require environmental evidence unless a future evidence-gated policy revision explicitly states otherwise.

## Evidence retained per inventory entry

Where present:

- exact IFC source SHA-256;
- STEP ID;
- GlobalId;
- IFC entity type and name;
- containment relationship identity;
- decomposition relationship identity;
- material-association relationship and material-select identity;
- `IfcElementQuantity` / quantity STEP identity;
- source STEP quantity lexical token;
- canonical Decimal quantity;
- parser numeric consistency value, explicitly non-authoritative;
- exact declared unit identity.

## Acceptance invariants

- exact source bytes are authority; file path is not;
- inventory ordering is STEP-ID ascending;
- duplicate STEP IDs fail closed;
- duplicate non-empty GlobalIds fail closed;
- zero enumerated objects fail closed;
- every enumerated object is classified exactly once;
- enumerated count must equal classified/output count;
- exact quantity lexical token is authority;
- network resolution is forbidden;
- source/resource budgets are enforced;
- no whole-building LCA, scientific validation, professional review, regulatory acceptance, or certification is inferred.

## Next action required for closure

Supply one actual `.ifc` model revision that the user authorizes ProofGrid to process. After the exact bytes are available, create the source-authorization manifest from that file SHA-256 and run the real two-hosted-runner gate. Until then, the correct status is:

`IMPLEMENTATION_READY_REAL_SOURCE_BLOCKED`

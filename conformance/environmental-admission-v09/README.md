# ProofGrid v0.9 — Evidence-Gated Environmental Declaration Admission

ProofGrid v0.9 composes the independently validated v0.6, v0.7, and v0.8 evidence dimensions into a fail-closed admission state machine.

It answers one bounded operational question:

> Given local source bytes and an explicit source-authority manifest, can ProofGrid verify authority and integrity, detect the ILCD+EPD version from content, route to the correct evidence gate, bind the resulting receipt to the exact source identity, and only then grant normalization permission?

It does **not** answer whether an environmental declaration is scientifically valid, representative of a real product, professionally reviewed, approved by a programme operator or BBSR, suitable for code/engineering/procurement decisions, or certified.

## State machine

```text
UNSEEN
  ↓
AUTHORITY_CHECKED
  ↓
SOURCE_INTEGRITY_VERIFIED
  ↓
FORMAT_VERSION_DETECTED
  ↓
ROUTE_SELECTED
  ↓
AWAITING_CONFORMANCE
  ↓
CONFORMANCE_RECEIPT_BOUND
  ↓
ADMITTED_FOR_NORMALIZATION
```

There is no supported transition from `UNSEEN`, `PARSED`, or `FORMAT_VERSION_DETECTED` directly to normalization.

### Phase 1 — preflight

Command:

```bash
python reference/environmental_admission.py preflight <package-dir> \
  --as-of YYYY-MM-DD \
  --output preflight.json
```

Successful bounded verdict:

`ENVIRONMENTAL_DECLARATION_ADMISSION_PREFLIGHT_VERIFIABLE`

Required state:

- `state = AWAITING_CONFORMANCE`
- `normalization_permitted = false`
- `certified = false`

Preflight performs, in order:

1. Draft 2020-12 source-authority manifest validation;
2. v0.6 authorization/use-policy decision;
3. terms-snapshot SHA-256 verification;
4. source-content SHA-256 verification;
5. safe XML/ZIP inspection;
6. deterministic `epd-version` detection from ILCD process dataset content;
7. declared/detected version equality;
8. route selection.

A filename alone is never version evidence.

## Version routes

### ILCD+EPD v1.2

Route token:

`OEKOBAUDAT_V12_PROFILE_3_8_0`

Required evidence:

`OEKOBAUDAT_V12_PROFILE_380_SYNTHETIC_AUTHORITY_SAFE_COMPATIBLE`

The admission engine requires a canonical receipt, `certified=false`, `authority_inference_allowed=false`, official-profile `error_count=0`, `is_positive=true`, and exact package-manifest binding.

The accepted v0.8 reference gate uses:

- `com.okworx.ilcd.validation:ilcd-validation:2.12.2`;
- `com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0`.

### ILCD+EPD v1.3

Route token:

`INDATA_V13_XSD_MASTERDATA_ONLY`

Required evidence:

`ILCD_EPD_V13_XSD_MASTERDATA_CONFORMANT`

The admission engine requires XSD conformance, selected master-data identity conformance, exact source-byte binding, `certified=false`, and `profile_validation_performed=false`.

The v1.2 ÖKOBAUDAT profile cannot be silently reused or relabeled as a v1.3 profile.

## Phase 2 — finalize

Command:

```bash
python reference/environmental_admission.py finalize \
  --preflight preflight.json \
  --conformance conformance.json \
  --output admission.json
```

Successful bounded verdict:

`ENVIRONMENTAL_DECLARATION_ADMISSION_PIPELINE_VERIFIABLE`

Required state:

- `state = ADMITTED_FOR_NORMALIZATION`
- `admitted = true`
- `normalization_permitted = true`
- `certified = false`

Finalization re-verifies the canonical preflight receipt, rejects preflight tampering, requires explicit transformation permission, verifies the route-specific conformance receipt, and binds that receipt to the exact source/package identity.

## Evidence dimensions remain independent

v0.9 deliberately preserves these as distinct states:

```text
AUTHORIZED
FORMAT_CONFORMANT
PROFILE_COMPATIBLE
SCIENTIFICALLY_VALID
PROFESSIONALLY_REVIEWED
CERTIFIED
```

A successful admission receipt establishes only the first applicable software/evidence gates. It never promotes unevaluated dimensions.

## ZIP safety / deterministic identity

For package sources, the router:

- rejects absolute or `..` member paths;
- rejects duplicate member paths;
- limits file count, individual uncompressed size, and total uncompressed size;
- requires one unambiguous `epd-version` across all `ILCD/processes/*.xml` process datasets;
- computes a deterministic content manifest over the ILCD tree;
- uses that content identity for v1.2 receipt binding.

## Mandatory fail-closed cases

The v0.9 test and hosted integration gates reject at least:

- missing authority manifest;
- `UNKNOWN` authorization;
- expired authorization;
- transformation prohibited;
- source-content hash mismatch;
- declared/detected format-version mismatch;
- unsupported version;
- mixed/ambiguous versions inside a ZIP;
- v1.2 profile errors;
- v1.2 package-manifest binding mismatch;
- v1.3 source-binding mismatch;
- v1.3 receipt that silently claims profile validation;
- `certified=true` promotion through the admission pipeline;
- tampered preflight receipt;
- v1.3 preflight paired with a v1.2 profile receipt;
- `EXPLICITLY_AUTHORIZED` manifest without an approval reference.

## Initial hosted implementation receipt

The first hosted implementation run on branch head

`e1bc78d776e28e7282a527d6fe7c1cb8a912eefb`

completed successfully:

- workflow: `ProofGrid v0.9 Environmental Admission`;
- run ID: `32446324881`;
- artifact ID: `9434188780`;
- artifact ZIP SHA-256: `80a5d58630d7f452be46ecc4332ef69ea8e7fee00f875283e849732230390178`;
- integration receipt SHA-256: `8655aeaac8ea791bb71a928d732dd2f2712a790028e2a553c2711e34f3e2c00f`;
- inherited `ProofGrid Genesis` run #40: success.

### v1.2 integration receipt

- source ZIP SHA-256: `21426e5479e2323d27c2f47d5e39379ff11e0457b7bc1c97b01c376dd76fe9c2`;
- package-manifest SHA-256: `0bf4bf1fc0880cc693ead60f775d9e631ff13b8e70e5be02482f3615ae2551aa`;
- preflight receipt SHA-256: `f44901b63e9f50a83f7f6bac6a6911d553e7c0eae1900b225ab1f51d77775d38`;
- conformance receipt SHA-256: `e7e26fcf035002699b2e6c4439c9e7996345531d02daaa166ab6f4f62d7a6100`;
- final admission receipt SHA-256: `5a8c7812fe50658aeab7c6e85cf78acb984ab4df9895b063e0b7000519fd3bf9`;
- official profile errors: `0`;
- warnings retained: `26`;
- `profile_validation_performed = true`;
- `normalization_permitted = true`;
- `certified = false`.

### v1.3 integration receipt

- source XML SHA-256: `7db95464214c68d6cf3cd9e3164e62d414d34b55e16c9a8133ee925947f04f16`;
- preflight receipt SHA-256: `887f8c2fcc8c969ed61f3d3c18d4a15126dc5b328b46cb49cca17325ffcf790e`;
- v0.7 conformance receipt SHA-256: `094f96b2ff3659a9b8fdb320dcf6bc91ad0e64ebfc5c0d474b3ea0ab860d338e`;
- final admission receipt SHA-256: `cc684aa2ef901383a88b597e274e39b98ee78a63c77feb687fb4f5ae013f53e1`;
- XSD validation: true;
- master-data identity validation: true;
- `profile_validation_performed = false`;
- `normalization_permitted = true`;
- `certified = false`.

The initial receipt remains historical implementation evidence. The final acceptance receipt for v0.9 must be taken from the documentation-complete exact head after this document is included in the hosted workflow trigger.

## Non-claims

A v0.9 admission receipt does not establish or imply:

- provider/source rights beyond the explicit manifest;
- redistribution rights unless independently authorized;
- scientific validity;
- real-product representativeness;
- professional LCA review;
- programme-operator acceptance or registration;
- BBSR plausibility approval or database import;
- code, engineering, architectural, procurement, or regulatory approval;
- certification.

**Attribution:** RegenExcalibur / 1JGM

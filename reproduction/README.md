# ProofGrid R5 Clean-Environment Reproduction Package

This package tests whether the frozen ProofGrid v0.4 implementation can be reproduced from published repository files in fresh execution environments with no unpublished local state and no manual correction during the run.

## Frozen implementation

`7a563256e2b1c035fef5779dd2c81be6ac8b84a9`

This is the bit-portable v0.4 head using verifier software `0.3.2` with deterministic calculation method `0.3.0`. The reproduction harness fails if declared core implementation paths differ from this commit.

### Portability defects that were found instead of waived

1. **OS-native receipt paths.** A Windows clean-environment run reproduced the known-answer result and evidence digest but not the RXEP receipt digest because repository-relative schema paths used `\\` on Windows and `/` on Linux. Verifier `0.3.1` canonicalized those paths to POSIX form.
2. **OS-native output newlines.** Linux and Windows then reproduced the same logical evidence and receipt hashes, but pretty-printed output files differed byte-for-byte because text writes produced LF on Linux and CRLF on Windows. Verifier `0.3.2` now writes the four primary environmental artifacts as explicit UTF-8/LF bytes.

The full v0.4 suite was re-run after each core correction before this reproduction manifest was refrozen.

## Exact runtime policy

The hosted reproduction matrix declares an exact CPython patch per operating-system family:

- Linux / Ubuntu 24.04: Python `3.11.16`
- Windows Server 2025: Python `3.11.9`
- both environments: exact packages in `requirements-proofgrid.txt`

The separate Windows patch is explicit rather than permissive: the hosted Windows setup catalog does not provision Python 3.11 security-only releases such as 3.11.16 as Windows binaries, while 3.11.9 is available. The manifest records this platform-specific runtime policy and the harness rejects any version other than the declared exact version for the current OS.

The same frozen ProofGrid implementation, dependency lock, inputs, logical hashes, byte hashes, and semantic assertions are used on both platforms.

## Reproduce

From a clean clone/check-out of this branch, use the exact Python patch declared for your platform, then run:

```bash
python -m pip install --disable-pip-version-check -r requirements-proofgrid.txt
python -m pip check
python reproduction/reproduce.py --output reproduction-receipt.json
```

A passing run prints:

```text
RESULT: CLEAN_ENVIRONMENT_REPRODUCED
NOT INDEPENDENT PROFESSIONAL OR SCIENTIFIC CERTIFICATION
```

and writes `reproduction-receipt.json` containing:

- frozen implementation commit and execution checkout SHA;
- proof that the core implementation diff is clean;
- declared runtime policy, actual runtime/platform, and exact dependency versions;
- input SHA-256 values;
- known-answer environmental result;
- exact evidence and RXEP receipt digests;
- exact byte hashes for all four primary environmental artifacts;
- fresh IFC source hash;
- IFC structural/extraction results;
- manual-correction state;
- deviations;
- limitations;
- reproduction-receipt SHA-256.

## Expected environmental result

The synthetic Alberta fixture must reproduce:

- verifier software `0.3.2`
- calculation method `0.3.0`
- `3860.0 kgCO2e`
- `VERIFIABLE`
- `certified: false`
- evidence-content SHA-256 `be07217cfeed805d737637d7b760ae987f403a6d3b121b202889790bbdf5c001`
- RXEP receipt SHA-256 `9fb074795aae8f5020a04fdd00b0b8730ddaac2a5294a98b3d409910976e7280`

The four primary artifact files must also be bit-for-bit identical to the frozen Linux reference hashes:

- `evidence.json`: `72e396ef5c16ad4ef95c16f73b9134a964cb0ab923f8e26a8d44a9c4a993e212`
- `graph.jsonld`: `909a41748afc9cc4b458ce2da5c03cb8310719f8cd3c35fc617bca9d3aa63ffe`
- `receipt.json`: `91645c1fb22d7f92adb7c7acfa332b34c139029a0ad26bbdf5929fa34d521eda`
- `report.html`: `85cf90ad6565772e5251bfd324475048e12934d425b90d09c621de4b35432fe3`

All inputs and environmental source-record digests are frozen in `r5-manifest.json`.

## Expected IFC result

The harness creates a fresh non-production IFC4 model and requires:

- one project;
- one building;
- one wall;
- `Concrete` material association;
- declared `Length = 3.5`;
- `LENGTHUNIT / METRE` unit context;
- `value_source = declared_ifc_element_quantity`;
- no environmental source-record linkage.

The fresh IFC file SHA may vary because the generated model contains new IFC GlobalIds. The semantic known-answer assertions above must not vary.

## Independence scope

A GitHub-hosted runner is an execution environment outside the implementation author's local machine and has no access to unpublished local files. However, the harness and acceptance assertions are themselves maintained in this repository.

Accordingly, the automated result is labeled **`CLEAN_ENVIRONMENT_REPRODUCED`**, not independent scientific validation or professional certification.

A reproduction by an unaffiliated human/researcher/organization using the worksheet in `WORKSHEET.md` is stronger evidence and should be retained if obtained.

## Fail-closed behavior

Any mismatch in frozen core paths, platform-specific exact runtime, dependency versions, input hashes, known-answer value, verifier/method versions, logical evidence digest, RXEP receipt digest, source-record digests, any of the four primary artifact byte hashes, or required IFC semantics causes a non-zero exit code.

No discrepancy is automatically repaired or waived.

## Non-production boundary

The Alberta project and environmental factors are synthetic. This reproduction does not establish real-building LCA, code compliance, engineering adequacy, architectural approval, procurement approval, regulatory approval, certification, or product-market fit.

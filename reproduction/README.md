# ProofGrid R5 Clean-Environment Reproduction Package

This package tests whether the frozen ProofGrid v0.4 implementation can be reproduced from published repository files in fresh execution environments with no unpublished local state and no manual correction during the run.

## Frozen implementation

`fe27d78171140832a7985e4d5157f5541c8a02aa`

This is the portability-patched v0.4 head using verifier software `0.3.1` with calculation method `0.3.0`. The reproduction harness fails if declared core implementation paths differ from this commit.

The prior frozen head `b0f3e0b4afbc7e787d7063f4b1cfa693083dd0d4` was intentionally superseded after a Windows clean-environment run discovered OS-native path separators inside the RXEP receipt. The calculation result and evidence-content digest reproduced, but the receipt digest differed. The defect was corrected by canonicalizing repository-relative schema paths to POSIX form, versioning the verifier, and re-running the entire v0.4 hosted gate before this manifest was refrozen.

## Exact runtime policy

The hosted reproduction matrix declares an exact CPython patch per operating-system family:

- Linux / Ubuntu 24.04: Python `3.11.16`
- Windows Server 2025: Python `3.11.9`
- both environments: exact packages in `requirements-proofgrid.txt`

The separate Windows patch is explicit rather than permissive: the hosted Windows setup catalog does not provision Python 3.11 security-only releases such as 3.11.16 as Windows binaries, while 3.11.9 is available. The manifest records this platform-specific runtime policy and the harness rejects any version other than the declared exact version for the current OS.

The same frozen ProofGrid implementation, dependency lock, inputs, expected hashes, and semantic assertions are used on both platforms.

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
- generated output hashes;
- fresh IFC source hash;
- IFC structural/extraction results;
- manual-correction state;
- deviations;
- limitations;
- reproduction-receipt SHA-256.

## Expected environmental result

The synthetic Alberta fixture must reproduce:

- `3860.0 kgCO2e`
- `VERIFIABLE`
- `certified: false`
- evidence-content SHA-256 `9ce99ff076f41390c254377bd06e9897c4b203a4b778fbfd09c350624545142c`
- RXEP receipt SHA-256 `44955751eec438621e43e2478e672a55bd6bff3aaf3a6e27ac588ff07cee8b7d`

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

Any mismatch in frozen core paths, platform-specific exact runtime, dependency versions, input hashes, known-answer value, evidence digest, RXEP receipt digest, source-record digests, or required IFC semantics causes a non-zero exit code.

No discrepancy is automatically repaired or waived.

## Non-production boundary

The Alberta project and environmental factors are synthetic. This reproduction does not establish real-building LCA, code compliance, engineering adequacy, architectural approval, procurement approval, regulatory approval, certification, or product-market fit.

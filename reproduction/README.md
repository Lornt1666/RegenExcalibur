# ProofGrid R5 Clean-Environment Reproduction Package

This package is designed to test whether the frozen ProofGrid v0.4 implementation can be reproduced from published repository files in a fresh execution environment with no unpublished local state and no manual correction during the run.

## Frozen implementation

`b0f3e0b4afbc7e787d7063f4b1cfa693083dd0d4`

The reproduction harness fails if the declared core implementation paths differ from that commit.

## Environment

Required runtime:

- Python `3.11.16`
- exact packages in `requirements-proofgrid.txt`
- Git checkout containing the frozen implementation commit in history

The hosted reproduction workflow executes the same harness on fresh GitHub-hosted Linux and Windows runners.

## Reproduce

From a clean clone/check-out of this branch:

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
- runtime/platform and exact dependency versions;
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
- evidence-content SHA-256 `d914a8faf3a387fd5919784102fa396298c2977af23789e75b024771cda7ef0d`
- RXEP receipt SHA-256 `2406b1a781cb10d2df0806200a1811d72de05d256fd06ba18b67511a2fbc4229`

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

Any mismatch in frozen core paths, runtime, dependency versions, input hashes, known-answer value, evidence digest, RXEP receipt digest, source-record digests, or required IFC semantics causes a non-zero exit code.

No discrepancy is automatically repaired.

## Non-production boundary

The Alberta project and environmental factors are synthetic. This reproduction does not establish real-building LCA, code compliance, engineering adequacy, architectural approval, procurement approval, regulatory approval, certification, or product-market fit.

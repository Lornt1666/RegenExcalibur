# ProofGrid R5 External Reproduction Worksheet

Use this worksheet for a reproduction performed by a person or organization not involved in implementing the tested ProofGrid slice.

Do not report a pass unless every claimed check was actually performed. Record discrepancies exactly as observed.

## Reproducer

- Name or public identifier:
- Organization / affiliation (if any):
- Role / relevant background:
- Relationship to RegenExcalibur / implementation author:
- Contact or public evidence reference (optional):
- Date/time (UTC):

## Frozen target

- Repository: `Lornt1666/RegenExcalibur`
- Implementation commit: `b0f3e0b4afbc7e787d7063f4b1cfa693083dd0d4`
- Reproduction manifest path: `reproduction/r5-manifest.json`
- Reproduction harness path: `reproduction/reproduce.py`

## Environment

- Operating system:
- CPU architecture:
- Python version:
- Git version:
- Network restrictions / proxy (if relevant):
- Clean clone or other acquisition method:
- Exact repository checkout SHA used:

## Installation

Commands executed:

```text

```

Did `pip check` report no broken requirements? `YES / NO`

Any installation deviation from `requirements-proofgrid.txt`?

```text

```

## Reproduction command

```text
python reproduction/reproduce.py --output reproduction-receipt.json
```

Actual command if different:

```text

```

## Required checks

Record `PASS`, `FAIL`, or `NOT RUN` plus evidence/notes.

| Check | Result | Evidence / notes |
| --- | --- | --- |
| Core implementation matches frozen commit | | |
| Python/runtime matches manifest | | |
| Locked dependencies match | | |
| Input SHA-256 values match | | |
| Draft 2020-12 validation succeeds | | |
| Known answer equals `3860.0 kgCO2e` | | |
| Evidence-content digest matches manifest | | |
| RXEP receipt digest matches manifest | | |
| Environmental source-record digests match | | |
| Result remains `VERIFIABLE`, not certified | | |
| IFC4 structural ingestion succeeds | | |
| IFC declared-data extraction succeeds | | |
| IFC wall/material/declared quantity known answer matches | | |
| No IFC→environmental source-record linkage appears | | |
| No manual correction was needed during the run | | |
| Reproduction receipt was retained | | |

## Key reproduced values

- Environmental known answer:
- Evidence-content SHA-256:
- RXEP receipt SHA-256:
- Reproduction receipt SHA-256:
- IFC source SHA-256:
- IFC declared quantity/value/unit:
- IFC material association:

## Deviations / discrepancies

```text

```

## Manual intervention

Were any files edited, values replaced, commands patched, tests disabled, warnings suppressed, or failed steps manually bypassed during the reproduction?

`YES / NO`

If yes, describe exactly:

```text

```

## Reproducer determination

Choose one:

- `PASS — reproduced from published inputs without manual correction`
- `FAIL — reproducibility discrepancy found`
- `INCONCLUSIVE — environment/setup prevented complete test`

Determination:

```text

```

## Boundary acknowledgement

This worksheet documents software reproducibility evidence only. It does not establish professional LCA review, environmental certification, code compliance, engineering or architectural approval, procurement approval, regulatory approval, or product-market fit.

Reproducer acknowledgement / signature or public attestation reference (optional):

```text

```

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
- Implementation commit: `7a563256e2b1c035fef5779dd2c81be6ac8b84a9`
- Verifier software: `0.3.2`
- Calculation method: `0.3.0`
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
| Python/runtime matches platform-specific manifest requirement | | |
| Locked dependencies match | | |
| Input SHA-256 values match | | |
| Draft 2020-12 validation succeeds | | |
| Verifier software equals `0.3.2` | | |
| Calculation method equals `0.3.0` | | |
| Known answer equals `3860.0 kgCO2e` | | |
| Evidence-content digest equals `be07217cfeed805d737637d7b760ae987f403a6d3b121b202889790bbdf5c001` | | |
| RXEP receipt digest equals `9fb074795aae8f5020a04fdd00b0b8730ddaac2a5294a98b3d409910976e7280` | | |
| `evidence.json` byte hash equals `72e396ef5c16ad4ef95c16f73b9134a964cb0ab923f8e26a8d44a9c4a993e212` | | |
| `graph.jsonld` byte hash equals `909a41748afc9cc4b458ce2da5c03cb8310719f8cd3c35fc617bca9d3aa63ffe` | | |
| `receipt.json` byte hash equals `91645c1fb22d7f92adb7c7acfa332b34c139029a0ad26bbdf5929fa34d521eda` | | |
| `report.html` byte hash equals `85cf90ad6565772e5251bfd324475048e12934d425b90d09c621de4b35432fe3` | | |
| Environmental source-record digests match manifest | | |
| Canonical schema paths use `/` separators | | |
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
- `evidence.json` SHA-256:
- `graph.jsonld` SHA-256:
- `receipt.json` SHA-256:
- `report.html` SHA-256:
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

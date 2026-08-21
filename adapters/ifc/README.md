# IFC Adapter

Status: **v0.4 declared quantity/material extraction implemented under conformance testing**.

ProofGrid uses IfcOpenShell behind an explicit adapter boundary. The structural inspection path from v0.2 remains available, and v0.4 adds a separate extraction path for IFC-declared quantities, project unit context, spatial hierarchy, and material associations.

## Commands

Structural inspection:

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
```

Declared-data extraction:

```bash
python reference/ifc_extract.py path/to/model.ifc --output ifc-extraction.json
```

## v0.4 extraction responsibilities

- parse real `.ifc` STEP files with pinned IfcOpenShell;
- preserve source-file SHA-256 and IFC schema;
- preserve project/site/building/storey/space STEP IDs, GlobalIds, names, types, and aggregation-parent identifiers;
- retain the project unit assignment and explicit quantity units where declared;
- extract supported values only when they are explicitly present in `IfcElementQuantity`;
- support declared length, area, volume, weight, count, and time quantity types;
- preserve `IfcMaterial`, material-layer-set, material-constituent-set, material-profile-set, and material-list associations where supported;
- preserve ambiguous/blank material names and emit warnings rather than inventing identities;
- retain duplicate/conflicting declared quantities and emit deterministic warnings rather than silently choosing one;
- validate the extraction artifact against `schemas/ifc-extraction.schema.json`.

## Unit rule

v0.4 reports values and unit context as declared. It does **not** convert units. For example, a declared value of `3500` with `MILLI` + `METRE` remains `3500` millimetres; it is not silently rewritten as `3.5` metres.

Any future conversion engine requires a separately versioned deterministic method, conversion provenance, known-answer fixtures, and its own evidence gate.

## Quantity rule

Only IFC-declared `IfcElementQuantity` values are treated as declared quantities in this slice. ProofGrid v0.4 does **not** calculate geometry-derived quantity takeoffs.

## Material rule

Material relationships are extracted from IFC associations. Material names are **not** fuzzy-matched to EPD/LCA/environmental source records. Missing or ambiguous names are warnings, not permission to infer an identity.

## Deliberately not implemented in v0.4

- geometry-derived takeoff;
- unit normalization or conversion;
- IFC material-name to environmental-factor matching;
- automatic IFC-to-LCA calculation;
- code-compliance inference;
- engineering or architectural conclusions;
- procurement approval;
- certification.

The v0.4 extractor therefore produces **evidence-controlled IFC input data**, not environmental or professional conclusions.

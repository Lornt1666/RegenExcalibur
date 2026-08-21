# IFC Adapter

Status: **v0.4 declared quantity/material extraction implemented; v0.5 may consume that extraction only through explicit reviewed mapping records**.

ProofGrid uses IfcOpenShell behind an explicit adapter boundary. The structural inspection path remains available, v0.4 provides evidence-controlled extraction of IFC-declared data, and v0.5 adds a separate mapping verifier that can bind exact extracted identities to exact environmental source records.

The IFC adapter itself does **not** choose environmental records.

## Commands

Structural inspection:

```bash
python reference/rx_cli.py ifc-inspect path/to/model.ifc --output ifc-summary.json
```

Declared-data extraction:

```bash
python reference/ifc_extract.py path/to/model.ifc --output ifc-extraction.json
```

Explicit v0.5 mapping verification/calculation:

```bash
python reference/ifc_lca_map.py \
  --extraction ifc-extraction.json \
  --mapping ifc-environmental-mapping.json \
  --registry lca-sources.json \
  --output ifc-environmental-mapping-receipt.json
```

## Extraction responsibilities

- parse real `.ifc` STEP files with pinned IfcOpenShell;
- preserve source-file SHA-256 and IFC schema;
- preserve project/site/building/storey/space STEP IDs, GlobalIds, names, types, and aggregation-parent identifiers;
- retain project unit assignment and explicit quantity units where declared;
- extract supported values only when explicitly present in `IfcElementQuantity`;
- support declared length, area, volume, weight, count, and time quantity types;
- preserve supported `IfcMaterial`, layer-set, constituent-set, profile-set, and material-list associations;
- preserve ambiguous/blank material names and emit warnings rather than inventing identities;
- retain duplicate/conflicting declared quantities and emit deterministic warnings rather than silently choosing one;
- validate the extraction artifact against `schemas/ifc-extraction.schema.json`.

## v0.5 mapping boundary

The mapping layer may use an extraction only when the mapping artifact exactly binds the relevant IFC evidence:

- source IFC SHA-256 and schema;
- element GlobalId, STEP ID, and IFC type;
- material association and material STEP IDs;
- exact declared material name and source type;
- quantity-set and quantity STEP IDs;
- quantity name, IFC quantity type, exact declared value, and unit declaration.

The mapping artifact must also explicitly name the target environmental `material_identity_id` and `source_record_id`.

A material name such as `Concrete` is evidence to be checked, **not a selector**. ProofGrid does not search for, infer, rank, or fuzzy-match an environmental factor from the material string.

## Quantity rule

Only IFC-declared `IfcElementQuantity` values are treated as declared quantities. ProofGrid does not calculate geometry-derived quantity takeoffs in this conformance path.

A v0.5 mapped quantity must retain `value_source = declared_ifc_element_quantity` and exactly match the mapping artifact's quantity identity and numerical value.

## Unit rule

Extraction reports IFC units as declared and performs no conversion.

The initial v0.5 mapping gate recognizes exactly one unit identity bridge:

```text
MASSUNIT + KILO + GRAM → kg identity
```

The numerical quantity is unchanged. `1000.0` remains `1000.0`; the bridge only states that the IFC declaration denotes kilograms for the narrow mapping gate. `numerical_conversion_applied` is therefore `false`.

No other conversion or normalization is authorized by v0.5.

## Material ambiguity rule

Blank or ambiguous IFC material names remain unmapped. A mapping artifact cannot turn missing IFC material identity into permission to guess an environmental target.

## Evidence-state boundary

A successful v0.5 mapping means that an explicit reviewed mapping record matched exact IFC extraction evidence and an exact provenance-controlled environmental source record, and that the declared deterministic calculation completed.

It does **not** mean:

- the IFC model is correct;
- the quantity is professionally verified;
- the environmental source is scientifically appropriate for a real project;
- the mapping was approved by a licensed professional merely because its workflow state is `REVIEWED`;
- an LCA, code-compliance, engineering, architectural, procurement, regulatory, or certification conclusion has been reached.

## Still deliberately out of scope

- geometry-derived takeoff;
- fuzzy or AI-autonomous environmental-factor selection;
- general unit conversion;
- production EPD/database ingestion;
- code-compliance inference;
- engineering or architectural conclusions;
- procurement approval;
- environmental certification.

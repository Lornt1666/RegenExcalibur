# ProofGrid v1.3 — Declaration / Reference Basis Research

ProofGrid v1.3 is stacked from accepted v1.2 head:

`9fbfa4f65863abcdc7be6becc4c5d0520f6d8d60`

The purpose of this layer is to resolve the dimensional **reference basis** behind source-declared environmental results before any quantity multiplication is permitted.

## Why this exists

The pinned InData ILCD+EPD example process contains a `quantitativeReference` that points to a reference-flow exchange. That exchange exposes both `meanAmount` and `resultingAmount`. Neither number may be selected as the declaration basis by inspection or convention alone.

The research lane must follow the actual referenced graph:

`process quantitativeReference`
→ `reference exchange`
→ `flow dataset`
→ `reference flow property`
→ `flow-property dataset`
→ `unit group`
→ `reference unit`

All cross-dataset resolution is by exact dataset UUID parsed from immutable XML content. Filenames and human-readable labels are not identity authority.

## Research constraints

The research receipt must preserve, without choosing a calculation basis:

- process UUID/version and quantitative-reference type;
- reference-flow internal ID;
- exact matching exchange;
- exchange `meanAmount` lexical + Decimal;
- exchange `resultingAmount` lexical + Decimal;
- referenced flow UUID/version/name and bytes;
- flow quantitative-reference / reference-flow-property relationship;
- referenced flow-property UUID/version/name and bytes;
- referenced unit-group UUID/version and bytes;
- reference-unit internal ID/name/factor;
- any additional material-property signals separately from the reference basis;
- every candidate dataset resolution path and its SHA-256.

The receipt must explicitly state:

```text
declaration_basis_selected = false
building_quantity_multiplication_permitted = false
unit_conversion_performed = false
scientific_validation_performed = false
professional_review_performed = false
certified = false
```

## No semantic shortcuts

The research layer must not:

- equate `meanAmount` with the declared unit without source-backed proof;
- equate `resultingAmount` with the declared unit without source-backed proof;
- infer a unit from a flow name;
- infer a flow-property dataset from a filename;
- treat a material property (for example density) as the declaration basis;
- treat the environmental-result unit (`kg CO2 eqv.`) as the product/reference unit;
- perform a building-level impact calculation.

## Research verdict

A successful research-only gate may emit:

`DECLARATION_BASIS_STRUCTURE_RESEARCH_VERIFIABLE`

That verdict means the exact reference graph was resolved reproducibly. It does **not** mean a declaration basis has been selected or accepted for calculation.

**Attribution:** RegenExcalibur / 1JGM

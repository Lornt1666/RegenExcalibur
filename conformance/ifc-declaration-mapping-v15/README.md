# ProofGrid v1.5 — Explicit IFC Material → Declaration Product Mapping

## Purpose

v1.5 creates the explicit identity bridge between one exact IFC material association and one exact accepted declaration product-flow identity.

Accepted declaration parent:

- v1.4.1 head `0a6d497aae056b4f36c2c6b0ccb067c363df6561`;
- verdict `DECLARATION_PRODUCT_IDENTITY_CLOSURE_BOUND_VERIFIABLE`.

Bounded mapping verdict:

`IFC_DECLARATION_PRODUCT_MAPPING_VERIFIABLE`

## Authority model

The mapping succeeds only through an explicit `REVIEWED_MAPPING_DECISION` artifact naming exact:

- IFC source SHA-256 and schema;
- element STEP ID + GlobalId + IFC type;
- material-association STEP ID;
- material STEP ID + exact declared source name/type;
- declared quantity-set and quantity STEP IDs;
- exact quantity value and IFC unit identity;
- v1.4.1 closure content/receipt SHA-256;
- declaration source/process identity;
- product-flow UUID **and version**;
- product-flow source SHA-256;
- declared reference quantity/unit.

Display-name similarity is not mapping authority.

The first hosted positive material label is intentionally:

`RX-MATERIAL-UNRELATED-TO-WOOD-PANEL`

while the accepted declaration product name remains `wood panel`.

## Unit boundary

The first control accepts only the already-proven identity bridge:

`IfcSIUnit(MASSUNIT, KILO, GRAM) → kg`

against declaration reference unit `kg`, with `numerical_conversion_applied=false`.

Plain grams or any other non-identity relation fail closed and require a separately specified conversion gate.

## No-calculation boundary

Successful v1.5 evidence remains:

- `mapping_method=EXPLICIT_REVIEWED_ARTIFACT`;
- `fuzzy_matching_performed=false`;
- `automatic_name_mapping_performed=false`;
- `environmental_calculation_performed=false`;
- `building_quantity_multiplication_performed=false`;
- `unit_conversion_performed=false`;
- `scientific_validation_performed=false`;
- `professional_review_performed=false`;
- `certified=false`.

The declared IFC mass is retained only as evidence. v1.5 does not multiply it by any environmental result.

## Review-state boundary

`REVIEWED_MAPPING_DECISION` means the artifact passed this workflow's explicit mapping-review state. It does not prove licensed professional review, engineering approval, LCA validation, programme-operator authority, regulatory approval, or certification.

**Tracks:** #42.

**Attribution:** RegenExcalibur / 1JGM

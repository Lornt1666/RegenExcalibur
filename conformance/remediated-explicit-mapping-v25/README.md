# ProofGrid v2.5 — Explicit Reviewed Mapping for Remediated Uncovered Element

This gate binds the accepted v2.4 successor IFC element/material/quantity identities to one accepted v1.4.1 declaration product identity using an explicit synthetic `REVIEWED_MAPPING_DECISION`.

Mapping authority is exact IDs + provenance. Display-name similarity is not authority.

The gate deliberately performs no environmental factor/result selection and no impact calculation.

Positive state:

- `mapping_state=EXPLICIT_REVIEWED_MAPPING`
- `environmental_mapping_performed=true`
- `environmental_source_identity_selected=true`
- `environmental_factor_selected=false`
- `impact_calculation_performed=false`
- `environmental_coverage_status=EVIDENCE_UNCOVERED`
- `fuzzy_mapping_performed=false`
- `professional_review_performed=false`
- `certified=false`

`REVIEWED_MAPPING_DECISION` is a synthetic workflow review state only. It does not imply professional licensure, scientific validity, programme-operator authority, regulatory approval, or certification.

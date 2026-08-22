# ProofGrid v2.2 — declared evidence-scope coverage ledger

v2.2 verifies one **declared synthetic evidence scope** containing exactly the two accepted semantic contributions from v1.9 and binds that coverage to the accepted v2.1 RXEP partial aggregate.

It deliberately does **not** evaluate or claim whole-building completeness.

## Declared scope

The manifest lists exactly two expected semantic contributions:

- `75eff1d5c89afbb44db7a709f8958c10bc6c46c52b96e7b6b56aab4ff8a5b950` → element `1CXL7DJx51bvggyIPU2Xi6`
- `b0c85f4123a5dbc6206cf3dc2ac08aed7626633c0a901a29e9fad395c67cf0dc` → element `1BXL7DJx51bvggyIPU2Xi5`

If both appear exactly once in the accepted v1.9 set, the ledger may report:

- `declared_scope_coverage_status=COVERED`
- `covered_member_count=2`
- `uncovered_member_count=0`
- `declared_scope_coverage_fraction_decimal=1`

`COVERED` applies only to this explicit two-member synthetic manifest.

## Hard boundaries

The result remains:

- `whole_building_scope=false`
- `whole_building_completeness_evaluated=false`
- `whole_building_lca_claimed=false`
- `declared_scope_complete_claimed=false`
- `missing_contributions_are_zero=false`
- `missing_modules_are_zero=false`
- `aggregation_recomputed=false`
- `scientific_validation_performed=false`
- `professional_review_performed=false`
- `certified=false`

Unlisted IFC elements, materials, systems, lifecycle modules, and other environmental contributions remain unknown/not evaluated.

## Accepted parents

- v1.9 set artifact `9464236551`, ZIP SHA-256 `38e24b2bcfcfcc227eeee5ac6cbaf79966aa838d27c7dc6b027637aad7b3297c`
- v2.1 RXEP aggregate artifact `9471587160`, ZIP SHA-256 `bf6ac1956787190b2aeda73f4ee4af6b004cc225e00310378d4be4b64bd99e59`

Bounded verdict:

`DECLARED_EVIDENCE_SCOPE_COVERAGE_VERIFIABLE`

This gate exists specifically to prevent a bounded PARTIAL result from silently becoming a whole-building claim.

**Attribution:** RegenExcalibur / 1JGM

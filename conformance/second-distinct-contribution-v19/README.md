# ProofGrid v1.9 — second distinct exact contribution

v1.9 creates the first genuinely distinct second environmental contribution needed before any multi-member aggregation gate can be specified.

The positive control uses a deterministic synthetic IFC4 file with:

- element GlobalId `1CXL7DJx51bvggyIPU2Xi6`;
- explicit `IfcRelAssociatesMaterial`;
- explicit `IfcQuantityWeight` of 500 kg;
- exact STEP numeric token retained by v1.5.1 as quantity authority;
- explicit reviewed synthetic mapping to the already accepted v1.3 declaration product identity;
- the exact source-declared `GWP-total / A1-A3 / scenario=null` row;
- Decimal-only scaling;
- RXEP `CALCULATED` evidence with exact Decimal authority.

Two independent hosted replicas must produce byte-identical IFC, mapping, quantity and calculation evidence before the second RXEP envelope is created.

The second contribution is then admitted alongside the original accepted v1.7 contribution through the unchanged v1.8 contribution-set engine. The resulting set must contain two different semantic identity hashes and remain `PARTIAL`.

No summation is performed.

Expected bounded second calculation:

`500 / 1 × 15.559479677163699 = 7779.7398385818495 kg CO2 eqv.`

The expected Decimal is derived from the source-authoritative quantity and declared environmental row. The parser float is never calculation authority.

## Non-claims

v1.9 does not establish a complete building LCA, scientific validation, professional review, regulatory approval, provider authority, or certification. It performs no set sum, unit conversion, scenario inference, missing-value zeroing, or fuzzy/name-only mapping.

**Attribution:** RegenExcalibur / 1JGM

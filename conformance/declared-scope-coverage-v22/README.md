# ProofGrid v2.2 — Declared-Scope Coverage / Partial Obligations

v2.2 performs **no environmental arithmetic**. It proves coverage membership for a deliberately synthetic three-slot declared scope.

## Synthetic scope

Required slots:

1. IFC GlobalId `1BXL7DJx51bvggyIPU2Xi5` — covered only by accepted semantic identity `b0c85f...`;
2. IFC GlobalId `1CXL7DJx51bvggyIPU2Xi6` — covered only by accepted semantic identity `75eff1...`;
3. `proofgrid:v22:unresolved-required-slot-1` — explicitly unresolved, with no environmental value.

The third slot is a test obligation used only to prove fail-closed completeness semantics. The manifest is `synthetic=true` and `real_project=false`.

## Accepted parents

v2.2 hard-pins accepted v2.1 RXEP evidence and accepted v2.0 contribution-member identities before evaluating coverage.

## Result

```text
declared_scope_slot_count = 3
covered_slot_count = 2
unresolved_slot_count = 1
coverage_status = PARTIAL
completeness_promotion_permitted = false
environmental_arithmetic_performed = false
```

Exact slot membership is authoritative. No coverage percentage is calculated or treated as authoritative in v2.2.

## Fail-closed rules

- exact slot IDs, GlobalIds, and semantic-identity hashes only;
- no fuzzy/name matching;
- one contribution cannot satisfy multiple slots;
- unresolved slots carry no contribution identity and no value;
- unresolved/missing scope is never zero by assumption;
- all three declared slots must remain present;
- completeness cannot be promoted while an unresolved slot exists.

## Non-claims

This gate does not establish a real-project or whole-building scope, complete building LCA, scientific validity, professional review, regulatory approval, or certification.

Bounded verdict:

`DECLARED_SCOPE_COVERAGE_PARTIAL_VERIFIABLE`

**Attribution:** RegenExcalibur / 1JGM

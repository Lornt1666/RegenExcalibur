# ProofGrid v2.12 — bounded synthetic inventory basis closure

This gate proves that the accepted v2.11 3/3 evidence refresh matches exactly the immutable three-member `basis.json` manifest in this directory.

## What `complete` means here

`bounded_scope_membership_complete=true` means **only** that the manifest itself declares exactly three members and v2.11 contains accepted evidence for those same three members exactly once.

It does **not** mean:

- the three-member manifest is a complete real IFC model;
- whole-model inventory completeness has been evaluated;
- whole-building completeness has been evaluated;
- a whole-building LCA has been produced;
- missing real-world objects or modules equal zero;
- scientific validation, professional review, regulatory approval, or certification has occurred.

## Exact basis

The manifest binds:

- `covered-first` → `1BXL7DJx51bvggyIPU2Xi5`;
- `covered-second` → `1CXL7DJx51bvggyIPU2Xi6`;
- `uncovered-third` historical entry → `1DXL7DJx51bvggyIPU2Xi7`, covered through its accepted successor source and semantic contribution.

The manifest file bytes are SHA-256-bound into the closure record and receipt.

Bounded verdict:

`BOUNDED_SYNTHETIC_INVENTORY_BASIS_CLOSURE_VERIFIABLE`

# Compiler Invariants

1. Source material is never empty.
2. Source SHA-256 is calculated from original UTF-8 bytes.
3. Encoded source contains no raw `<` or `>`.
4. Encoded source round-trips to the original.
5. Runtime contains exactly one compiler-owned `</SOURCE_MATERIAL>` delimiter.
6. Universal kernel modules are always present.
7. Selected modules are unique.
8. Exactly one operation module is selected.
9. `DO_NOT_EXECUTE` is the default.
10. Consequential mode has a non-empty exact action allowlist.
11. An action cannot be both authorized and prohibited.
12. Foundry prompt-package completion does not imply project execution.
13. Refinement passes remain between one and five.
14. A context ceiling is enforced when explicitly supplied.
15. Validation failure blocks package release.

# Requirements Traceability

| Requirement | Design element | Test/evidence | RC1 state |
|---|---|---|---|
| AUTH-001 | Runtime kernel and authority module | Prompt inspection; module resource | Satisfied |
| AUTH-002 | `DO_NOT_EXECUTE` default | Request model; unit tests | Satisfied |
| AUTH-003 | Consequential action validation | Tests 13–14 | Satisfied |
| AUTH-004 | Exact authorized-action list in PIR | Test 14 | Satisfied |
| INTENT-001 | Intent kernel and PIR objective | Package inspection | Satisfied |
| INTENT-002 | PIR invariant list | Schema and package structure | Satisfied structurally; semantic preservation requires model evaluation |
| INTENT-003 | Intent module | External evaluation pending | Partially satisfied |
| LING-001 | Operation and domain modules | External evaluation pending | Partially satisfied |
| LING-002 | Kernel/modules operationalize vague terms | External evaluation pending | Partially satisfied |
| PIR-001 | `_build_pir` | Package compilation tests | Satisfied |
| ROUTE-001 | Ordered deterministic router | Tests 1–10; 120-case conformance | Satisfied |
| ROUTE-002 | Conditional module selection | Tests 6–10; conformance | Satisfied for seeded rules |
| DOMAIN-001 | Domain module reasons | RoutingDecision reasons | Satisfied structurally |
| OCC-001 | Professional-boundaries module | Built-environment test | Satisfied structurally |
| TOOL-001 | Tooling module and PIR lists | Package inspection | Satisfied structurally |
| TOOL-002 | Kernel/tooling prohibition | External model evaluation pending | Partially satisfied |
| EVID-001 | Evidence module | Package inspection | Satisfied structurally |
| EVID-002 | Kernel/evidence prohibitions | External adversarial evaluation pending | Partially satisfied |
| EVID-003 | Research module | Research corpus family | Satisfied structurally |
| SEC-001 | Untrusted source block | Test 11 | Satisfied |
| SEC-002 | JSON serialization, Unicode escape, delimiter count | Tests 11–12 | Satisfied for implemented encoder |
| PRIV-001 | Security and tooling modules | Security review | Satisfied structurally |
| COMP-001 | Separate Foundry/project states | Package and schema | Satisfied |
| COMP-002 | Runtime terminal rule | Prompt inspection | Satisfied structurally |
| COMP-003 | Completion module | External model evaluation pending | Partially satisfied |
| COMP-004 | Terminal rule | External model evaluation pending | Partially satisfied |
| REFINE-001 | Pass range validation and runtime field | Request validation | Satisfied |
| INNOV-001 | Innovation module | Completion corpus family | Satisfied structurally |
| SUPER-001 | Innovation module comparator requirements | External evaluation pending | Partially satisfied |
| EVAL-001 | Evaluation documentation and release manifest | Manual review | Satisfied |
| EVAL-002 | RC status remains evaluation pending | Manifest | Satisfied |
| CTX-001 | Conditional modules and optional context budget | Tests and compiler | Satisfied structurally |
| PROV-001 | SHA-256, package version, modules, validation | Tests 11–12 | Satisfied |

## Interpretation

“Satisfied structurally” means the deterministic compiler emits the required control. It does not mean every target language model will obey it. Requirements dependent on semantic model behaviour remain partially satisfied until external model and human evaluation produce evidence.

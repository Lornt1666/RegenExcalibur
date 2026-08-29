# Schema Matrix

| Contract | Input/output role | Runtime validation |
|---|---|---|
| FoundryRequest | Compiler input | Implemented by `FoundryRequest.from_dict` and request validator |
| PIR | Internal/inspectable task contract | Constructed deterministically; JSON Schema supplied |
| PromptPackage | Compiler output | Deterministic package validator plus JSON Schema |
| ValidationReport | Gate report | Constructed by validator; JSON Schema supplied |
| External evaluation case | Independent benchmark input | Documentation schema; harness pending |

Native provider schema enforcement is adapter/deployment-specific. The provider-neutral core remains usable without external dependencies.

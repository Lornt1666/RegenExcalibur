# Structured Outputs

PromptOS defines four JSON contracts:

- FoundryRequest
- Prompt Intermediate Representation
- PromptPackage
- ValidationReport

The schemas constrain fields and enumerations, but a schema-valid package can still contain semantically weak prose. Schema validation is therefore a hard structural gate, not a replacement for model or human evaluation.

Deployments that support native schema-constrained outputs should use these contracts or an equivalent derived schema. Deployments that do not support them should validate returned JSON after generation and reject malformed packages.

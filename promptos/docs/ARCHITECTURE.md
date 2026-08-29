# PromptOS v4.0 RC1 Architecture

## Design decision

The v3.2 Foundry is preserved as a normalized constitution. It is not injected wholesale into every task. PromptOS compiles a task-specific runtime prompt from five layers:

1. **Kernel** — intent fidelity, source trust boundary, evidence integrity, authority ceiling, completion truthfulness, bounded refinement.
2. **Operation module** — create, repair, merge, audit, optimize, adapt, compress, expand, translate, reverse-engineer, or standardize.
3. **Domain modules** — research, software, built environment, creative, business, education, innovation, definitive completion, security, tooling, or professional boundaries.
4. **Model adapter** — provider-neutral reasoning, OpenAI reasoning, fast-model, or local-small-model conventions.
5. **Task contract** — PIR, escaped source material, output contract, and terminal rule.

## Data flow

```text
FoundryRequest
    │
    ├── request validation
    │
    ├── deterministic operation routing
    │
    ├── deterministic module selection
    │
    ├── risk classification
    │
    ├── adapter selection
    │
    ├── source SHA-256 + delimiter-safe serialization
    │
    ├── PIR construction
    │
    ├── runtime prompt compilation
    │
    └── package validation
          ↓
      PromptPackage
```

## Deterministic boundaries

The following behaviour is deterministic:

- enum and request validation;
- operation rule precedence;
- module keyword routing;
- risk classification;
- adapter selection;
- source encoding and hashing;
- PIR field construction;
- required kernel-module checks;
- authority checks;
- corpus generation and partitioning.

The following remains probabilistic when a language model consumes the runtime prompt:

- semantic interpretation of ambiguous source material;
- domain reasoning;
- prompt drafting quality;
- creative synthesis;
- research synthesis;
- final response quality.

PromptOS therefore treats deterministic conformance as necessary but insufficient. External model and human evaluation remain separate release gates.

## Routing precedence

1. Explicit operation supplied by the caller.
2. MERGE.
3. AUDIT.
4. REPAIR.
5. COMPRESS.
6. ADAPT.
7. TRANSLATE.
8. REVERSE_ENGINEER.
9. STANDARDIZE.
10. OPTIMIZE.
11. EXPAND.
12. CREATE fallback.

MERGE precedes REPAIR so “merge these prompts and fix contradictions” is not reduced to a repair of only one source.

## Module economy

Four kernel modules are always loaded: `intent`, `evidence`, `authority`, and `output_contract`. Exactly one operation module is loaded. Domain modules are added only when deterministic conditions match. The runtime excludes unrelated discipline catalogues.

## Completion semantics

The compiler itself returns `PROMPT_PACKAGE_COMPLETE` after successful validation. It does not infer that the underlying project has been implemented. Under `DO_NOT_EXECUTE`, the underlying state is always `PROJECT_NOT_EXECUTED`, even when the compiled prompt targets an implementation-ready design.

## Multi-agent boundary

The RC implements one deterministic compiler process. Its disciplinary roles are prompt modules, not independently executing agents. A future multi-agent runtime must define separate contexts, identities, handoffs, authority, state, and evidence before using that label.

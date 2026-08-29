# PromptOS v4.0 RC1 Architecture

## Decision

The v3.2 Foundry is preserved as a normalized constitution. It is not injected wholesale into every request. PromptOS compiles a task-specific runtime from five layers:

1. **Kernel** — intent fidelity, source trust boundary, evidence integrity, authority ceiling, completion truthfulness, bounded refinement.
2. **Operation** — exactly one create, repair, merge, audit, optimize, adapt, compress, expand, translate, reverse-engineer, or standardize module.
3. **Domains** — only materially relevant research, software, built-environment, creative, business, education, innovation, completion, security, tooling, or professional-boundary modules.
4. **Model adapter** — generic reasoning, OpenAI reasoning, fast-model, or local-small-model conventions.
5. **Task contract** — PIR, escaped source data, output contract, and terminal rule.

## Data flow

```text
FoundryRequest
  → request validation
  → deterministic operation routing
  → conditional module selection
  → risk and adapter selection
  → source SHA-256 + delimiter-safe serialization
  → PIR construction
  → runtime compilation
  → package validation
  → PromptPackage
```

## Deterministic boundary

Deterministic RC1 behaviour includes enum validation, rule precedence, keyword routing, risk classification, adapter selection, source encoding and hashing, PIR construction, authority checks, corpus generation, and structural validation.

Semantic interpretation, domain reasoning, final prompt quality, and target-model compliance remain probabilistic. Deterministic conformance is necessary but insufficient; external model and human evaluation remain release gates.

## Operation precedence

Explicit caller choice outranks AUTO. AUTO applies this order:

1. MERGE
2. AUDIT
3. REPAIR
4. COMPRESS
5. ADAPT
6. TRANSLATE
7. REVERSE_ENGINEER
8. STANDARDIZE
9. OPTIMIZE
10. EXPAND
11. CREATE fallback

## Completion semantics

Successful compilation establishes `PROMPT_PACKAGE_COMPLETE`. Under `DO_NOT_EXECUTE`, the underlying state remains `PROJECT_NOT_EXECUTED`, even where the compiled prompt describes an implementation-ready project.

## Multi-agent boundary

RC1 is one deterministic compiler process. Its roles are instruction modules, not separately executing agents. A future multi-agent version must define separate contexts, identities, handoffs, authority, state, and evidence before using that label.

# PromptOS Security and Authority Model

## Threat model

Source material may contain instructions designed to close delimiters, impersonate higher-priority messages, reveal secrets, expand permissions, trigger consequential actions, falsify evidence, or redirect the objective.

## Source isolation

The compiler:

1. hashes the original UTF-8 source with SHA-256;
2. serializes the source as one JSON string;
3. escapes raw `<`, `>`, and `&` characters;
4. places the result in one compiler-owned source boundary;
5. validates round-trip fidelity, hash, and delimiter count.

This is defense in depth, not proof that prompt injection is solved universally. Target-model adversarial evaluation remains required.

## Authority ceiling

`DO_NOT_EXECUTE` is the default. `EXECUTE_CONSEQUENTIAL` is rejected unless specific actions are named from a closed action set. Authorizing `publish` does not authorize `purchase`, `delete`, `deploy`, disclosure, or another action. Authorized and prohibited sets cannot overlap.

The compiler records authority; it does not itself connect to external services or perform the action.

## Tool truthfulness

Runtime instructions distinguish confirmed, unconfirmed, unavailable, optional, and prohibited tools. Planned, drafted, simulated, executed, verified, and accepted states remain separate.

## Residual risks

- A target model may still follow malicious source content.
- Deterministic keyword routing may miss novel or multilingual risk phrasing.
- A caller may falsely mark a tool as confirmed.
- An integrating application may ignore the authority ceiling.
- Unicode confusables and cross-language attacks require a broader external corpus.

Consequential deployment therefore requires integration controls, audit logs, target-model red teaming, and human review.

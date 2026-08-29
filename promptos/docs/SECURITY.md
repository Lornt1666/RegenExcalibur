# PromptOS Security and Authority Model

## Threat model

PromptOS assumes source material may contain malicious or misleading instructions designed to:

- close a delimiter;
- impersonate a higher-priority instruction;
- reveal secrets;
- expand tool permissions;
- trigger publication, submission, purchase, deletion, deployment, or disclosure;
- falsify evidence or completion;
- redirect the objective.

## Source isolation

The compiler:

1. hashes the original UTF-8 source with SHA-256;
2. serializes the source as one JSON string;
3. converts raw `<`, `>`, and `&` characters into Unicode escape sequences;
4. places the result in a single source-material boundary;
5. instructs the target model to treat the block as data.

The original source therefore cannot contribute a raw closing tag to the compiled prompt. The validation layer checks round-trip fidelity, raw angle brackets, provenance hash, and delimiter count.

This is defense in depth, not a claim that prompt injection is solved universally. Model behaviour still requires adversarial evaluation.

## Authority ceiling

`DO_NOT_EXECUTE` is the default.

`EXECUTE_CONSEQUENTIAL` is rejected unless at least one specific action is named from the closed action set. Supplying `publish` does not authorize `purchase`, `delete`, `deploy`, or any other action. Prohibited and authorized action sets cannot overlap.

The compiler records authority; it does not itself connect to external services or perform the action.

## Tool truthfulness

Runtime instructions require tools to be classified as confirmed, unconfirmed, unavailable, optional, or prohibited. Planning, drafting, simulation, execution, verification, and acceptance are distinct states.

## Secrets and privacy

Credentials, private keys, API secrets, recovery codes, session tokens, authentication cookies, and unnecessary personal data should be represented by placeholders and supplied through secure deployment mechanisms rather than prompt text.

## Residual risks

- A target model may still follow malicious content despite the boundary.
- Keyword routing may miss novel risk phrasing.
- A caller may misclassify a tool as confirmed.
- An application integrating PromptOS may ignore the compiled authority ceiling.
- Unicode or language variants may require broader adversarial cases.

These risks require model-level red teaming, integration controls, audit logs, and human review before consequential production use.

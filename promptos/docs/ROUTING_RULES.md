# Deterministic Routing Rules

## Operation precedence

Explicit caller selection overrides AUTO. AUTO evaluates rules in this order:

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

The router records a human-readable reason for the selected operation.

## Universal modules

Every runtime includes:

- `intent`
- `evidence`
- `authority`
- `output_contract`
- exactly one `operation:*` module

## Conditional modules

| Module | Representative deterministic triggers |
|---|---|
| research | research, primary source, citation, literature, prior art, current verification, latest |
| software | software, code, API, repository, compiler, database, cloud, deployment, web/mobile app |
| built_environment | house, building, architecture, structural, HVAC, plumbing, construction, blueprint |
| creative | image, video, film, story, visual design, branding, animation, cinematic |
| business | business, market, customer, revenue, commercial, finance, product strategy |
| education | teach, lesson, curriculum, training, learner, assessment |
| innovation | next-generation, breakthrough, novel, category leader, better than, innovation |
| definitive_completion | definitive completion, implementation-ready, fully finished, complete product, completion record, finish the project |
| security | security, privacy, authentication, authorization, prompt injection, secret, credential |
| tooling | confirmed/unconfirmed tools or external-action terms |
| professional_boundaries | medical, legal, financial, structural, electrical, regulated, safety |

These rules are intentionally inspectable. They are a conservative RC baseline, not a claim of complete natural-language understanding.

## Adapter routing

- OpenAI/GPT identifiers → `openai-reasoning`
- fast/mini/low-latency identifiers → `fast-model`
- local/small-model identifiers → `local-small-model`
- otherwise → `generic-reasoning`

## Risk routing

- Safety-critical engineering, medical emergency/diagnosis, life safety, fire protection, or critical infrastructure → `SAFETY_CRITICAL`
- Consequential mode or explicit send/publish/submit/purchase/delete/production wording → `HIGH`
- Confirmed tools or non-default execution modes → `MODERATE`
- Otherwise → `LOW`

## Evolution rule

Routing rules may change only with:

1. an observed misroute;
2. a linked test case;
3. a proposed minimal correction;
4. regression evaluation;
5. a recorded decision.

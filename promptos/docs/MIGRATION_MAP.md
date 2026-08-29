# Migration Map: v3.2 Foundry → PromptOS v4.0 RC1

| v3.2 concern | v4.0 location |
|---|---|
| System purpose and trust boundary | normalized constitution; runtime kernel |
| Foundry operations | `FoundryOperation`; `operation:*` modules |
| Underlying task modes | `UnderlyingTaskMode`; request validation |
| Intent reconstruction | `intent` module; PIR objective and requirements |
| Clarification and assumptions | runtime kernel; PIR assumptions/blockers |
| Prompt Intermediate Representation | `_build_pir`; `pir.schema.json` |
| Academic and occupational routing | conditional domain modules; routing reasons |
| Linguistic compiler | operation/domain modules; model adapter |
| Prompt architecture selection | deterministic operation plus module set |
| Software and systems protocol | `software` module |
| Research and evidence protocol | `research` and `evidence` modules |
| Built-environment protocol | `built_environment` and `professional_boundaries` modules |
| Creative protocol | `creative` module |
| Business and education protocols | `business` and `education` modules |
| Tool/capability audit | `tooling` and `authority` modules |
| Data protection and source isolation | source encoder; `security` module |
| Prompt Evolution Without Infinity | `definitive_completion`; max pass validation |
| Breakthrough and superiority claims | `innovation` module |
| Quality gates | deterministic package validator; external evaluation plan |
| Output modes | `OutputMode`; compiled output contract |
| Context control | conditional modules; optional context budget |
| Terminal states | PIR and runtime terminal rule |
| Provenance | source SHA-256; manifest; requirement registry |

## Deprecated runtime patterns

The following v3.2 patterns remain conceptually represented but are not copied into every runtime:

- complete discipline catalogues;
- complete occupational catalogues;
- ceremonial multi-persona descriptions;
- repeated prohibitions appearing in several sections;
- fixed output packages irrelevant to the selected operation;
- unconditional project-completion records for simple tasks;
- universal claims of maximality or perfection;
- fixed recursion counts treated as proof of quality.

## Compatibility principle

The constitution remains the human-auditable source. PromptOS is the executable compilation layer. A requirement is not considered removed merely because its prose is absent from a particular runtime; it is either represented by the kernel, loaded conditionally, or recorded as non-applicable by the router.

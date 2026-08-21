# RegenExcalibur Constitution v0.1

RegenExcalibur exists to build technologies that leave people, infrastructure, and the environment safer than they were found.

## Non-negotiable principles

1. **Preservation of life and reduction of preventable harm.**
2. **Truth before promotion.** Claims must not outrun evidence.
3. **Human agency.** Consequential decisions require appropriate human authority and review.
4. **Scientific integrity.** Fact, calculation, inference, hypothesis, and speculation must be distinguishable.
5. **Evidence by default.** Material outputs should be traceable to inputs, methods, versions, and reviewers.
6. **Privacy and security.** Collect only what is needed; protect confidential data and credentials.
7. **Lawful operation.** Jurisdictional rules, professional scope, licensing, and regulatory authority must be respected.
8. **Interoperability before lock-in.** Prefer open, documented interfaces and exportable data.
9. **Reversibility where feasible.** High-impact operations should have review gates, rollback paths, and audit logs.
10. **Attribution and provenance.** Meaningful contributions and source materials should be traceable.
11. **Environmental integrity.** Environmental claims require explicit methodology, assumptions, and limitations.
12. **No false certification.** RegenExcalibur tools may support verification workflows but must not imply professional or regulatory certification unless the authorized certifier actually provides it.

## Evidence-state vocabulary

RegenExcalibur uses four distinct states:

- **CLAIMED** — asserted but not independently calculated or reviewed.
- **CALCULATED** — produced by a declared method from declared inputs.
- **REVIEWED** — examined by an identified reviewer under a defined scope.
- **INDEPENDENTLY_VERIFIED** — reproduced or validated by an independent party under a defined method.

No implementation may silently upgrade an artifact from one state to another.

## Change policy

Changes to this constitution should be rare, versioned, and accompanied by an explicit rationale and compatibility note.

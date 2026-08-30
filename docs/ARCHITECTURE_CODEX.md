# RegenExcalibur Architecture Codex — Phase I Omni-Scan

Status: **DRAFT SOURCE OF TRUTH — 2026-08-30**
Scan scope: all repositories owned by `Lornt1666` visible to the authenticated Grok GitHub connector.
Does not claim completeness of private file interiors or unindexed blobs.

---

## 1. Product definition

RegenExcalibur is a constellation, not a single app:

- **OS / prompt compiler:** PromptOS (v4.0 RC1 → v4.5 RC1) inside `Lornt1666/RegenExcalibur`
- **Cloud / IaC scaffold:** GCP Terraform + Cloud Run / Functions / Pub/Sub / Vertex AI packaging in the same repo (`RegenExcalibur_Project/`)
- **Autonomous worker:** `Lornt1666/AIGC` (FastAPI-class worker, governance, memory, 125 open issues)
- **Video pipeline:** `Lornt1666/OmniVidz`
- **Physical / lab twin:** `Lornt1666/rx-lab-simulation-emulator` (RX-LSE)
- **Public face:** `Lornt1666/RegenExcalibur-Webpage` + `-Cloud` + private twin
- **Product surface (new):** `Lornt1666/tcg` — RegenExcalibur AutoHouse (Coventry is visual/template reference only)
- **Support / experiments:** Eth-Faucet / Faucet-eth, contract-intelligence, throughput-justlornt95-api-forge, openai/codex fork

Commercial north star already encoded in PromptOS docs: AutoDesign / AutoEngineer / AutoAudit as paid conversion, BYOK so the customer pays the model provider, PromptOS meters orchestration separately. Pricing, licence activation, and payment processors remain **owner-gated**.

---

## 2. Repo map (constellation topology)

### Core spine (coordinate first)

| Repo | Visibility | Default branch | Open issues | Last push | Role |
| --- | --- | --- | --- | --- | --- |
| [RegenExcalibur](https://github.com/Lornt1666/RegenExcalibur) | public | `main` | 63 | 2026-08-29 | Flagship: GCP scaffold + PromptOS + freelance profile |
| [AIGC](https://github.com/Lornt1666/AIGC) | private | `main` | 125 | 2026-08-20 | Autonomous API Worker / cockpit / governance |
| [OmniVidz](https://github.com/Lornt1666/OmniVidz) | private | `main` | 11 | 2026-08-26 | Cloud video generation pipeline |
| [tcg](https://github.com/Lornt1666/tcg) | private | `RegenExcalibur-Webpage` | 0 | 2026-08-30 | AutoHouse product workspace (TypeScript) |
| [rx-lab-simulation-emulator](https://github.com/Lornt1666/rx-lab-simulation-emulator) | private | `main` | 2 | 2026-07-23 | RX-LSE laboratory twin |

### Public satellite

| Repo | Role |
| --- | --- |
| RegenExcalibur-Webpage | Conglomerate site (HTML), default branch oddly named `RegenExcalibur-Webpage` |
| RegenExcalibur-Cloud | Cloud terminal UI |
| Eth-Faucet | Base Sepolia faucet claimer |
| contract-intelligence | Template catalog + agreement-finder agent |

### Private / archival satellite

| Repo | Role |
| --- | --- |
| RegenExcalibur-Webpage-private | Early private twin of the webpage |
| Faucet-eth | Private faucet experiment |
| throughput-justlornt95-api-forge | API forge experiment |

### Default-branch anomaly

Several older repos use `RegenExcalibur-Webpage` as default branch instead of `main`. That is a constellation consistency defect. Do not silently rename; migrate with a documented cutover.

---

## 3. Flagship interior — `Lornt1666/RegenExcalibur` @ `main` `24c5b579`

Observed root:

- `README.md` — freelance profile first, then GCP scaffold
- `FREELANCE_PROFILE.md`
- `SECURITY.md`
- `RegenExcalibur_Project/` + matching zip
- `shortcut-bridge/`
- `.github/`

`main` does **not** yet contain the PromptOS tree. PromptOS lives on feature branches and draft/merged PRs:

| PR | Title | State |
| --- | --- | --- |
| #111 | PromptOS v4.0 RC1 | open draft |
| #113 | PromptOS v4.0 RC1 clean candidate | open draft |
| #114 | monetization + AutoDesign/AutoEngineer | open draft |
| #116 | v4.1 secret-safe BYOK preflight | open draft |
| #118 | v4.2 Requirement Graph + Prompt IR v2 | **merged** into feature line |
| #120 | v4.3 local BYOK runner | **merged** into feature line; hosted CI green |
| #121 | v4.4 in-memory control-plane stub | **merged** into feature line |
| #124 | v4.5 failure-localized recompilation | open draft |

Implication: the Source-of-Truth for PromptOS is the `feat/promptos-byok-runtime` line, not `main`. Phase II must decide the promotion path: squash-merge a clean PromptOS tree onto `main` behind CI, or keep `promptos/` isolated until evaluation closes.

GCP scaffold on `main` is an initial generated package. README itself says: ready for local review and dry-run, not claimed production deploy.

---

## 4. AIGC interior (worker OS)

AIGC is the densest implementation surface: `src/`, `tests/`, `schemas/`, `governance/`, `memory/`, `workflows/`, `infra/`, `prompts/`, Docker/Fly/Render, `ARCHITECTURE.md`, `AIGC_MASTER_PROMPT.md`, `OMEGA_X_CONSTITUTION.md`, `AGENTS.md`.

125 open issues is a coordination risk. Treat AIGC as the **runtime twin** of PromptOS, not a second compiler. Integration contract to design in Phase II:

- PromptOS compiles FoundryRequest → PIR / IR v2 → PromptPackage
- AIGC executes authorized packages behind judgment gates
- receipts stay secret-free and hash-chained (v4.4 ledger pattern)

---

## 5. Gaps, inconsistencies, incomplete threads

1. **Two truths on `RegenExcalibur`:** `main` = GCP zip scaffold + freelance README; feature branches = PromptOS v4.x. Public visitors see the scaffold, not the compiler.
2. **No constellation README** that links AIGC, OmniVidz, tcg/AutoHouse, RX-LSE, Webpage, Cloud.
3. **Issue load:** 63 (RegenExcalibur) + 125 (AIGC) + 11 (OmniVidz) with no shared triage taxonomy.
4. **Default branch naming drift** (`RegenExcalibur-Webpage` vs `main`).
5. **Duplicate faucet repos** (public Eth-Faucet + private Faucet-eth).
6. **Webpage public/private twin** — unclear which is canonical for regenexcalibur.xyz.
7. **PromptOS evaluation engine** that *produces* FailureReport is explicitly not implemented (#124).
8. **Control plane** is in-memory stub only (#121). No network server, no payments.
9. **Professional boundary** is documented but easy to overclaim in mythic prompts. Keep AutoEngineer = spec + coordination, not sealed engineering.
10. **tcg/AutoHouse** is brand-new (created 2026-08-29) and is the physical-product wedge; not yet wired to PromptOS AutoDesign.
11. **ZIP + expanded tree** duplication in the flagship repo.
12. **Onboarding > 30 minutes** across 12 repos with no single map (this Codex is the start of that map).

---

## 6. Unified configuration schema (proposed, not implemented)

Parametric surfaces that should become one schema family:

- `constellation.repos[]` — owner, name, visibility, default_branch, role, integration_contract
- `promptos.version` — 4.x-rcN, feature branch, evidence state
- `byok.provider_profile` — openai | anthropic | gemini | reviewed-custom
- `control_plane.mode` — in_memory | hosted (hosted = future)
- `gcp.project_id`, `region`, `apply` (default false)
- `aigc.judgment_gates`, `memory_backend`
- `autohouse.product_id`, `reference_only_templates[]`
- `commercial.service_units` — abstract; not currency

Do not hard-code conceptual decisions in application code. Put them here first.

---

## 7. Priority completion tasks (Phase I output)

Ordered by leverage, not mythology.

1. **Accept this Codex** as the evolving SoT (this PR).
2. **Choose PromptOS promotion path** — keep isolated vs merge clean `promptos/` onto `main` after CI + owner review. Do not merge drafts #111/#113/#114/#116/#124 blindly; they stack.
3. **Write a constellation index** into flagship README (link table above) without burying the freelance profile.
4. **Triage AIGC issues** into: runtime-now / PromptOS-contract / wontfix / duplicate. 125 undifferentiated issues block Omni-Evolve.
5. **Define the AIGC ↔ PromptOS IR v2 contract** (package in, receipt out, no secrets).
6. **Wire tcg/AutoHouse** as the first AutoDesign vertical (parametric house, Coventry reference-only).
7. **Normalize default branches** on satellite repos in a dedicated cutover PR per repo.
8. **Archive or mark** Faucet-eth / Webpage-private as historical.
9. **Do not** enable GCP `--apply`, payments, or control-plane hosting in this cycle.
10. **Close the evaluation gap** (#123/#124): FailureReport producer before claiming v4.5 complete.

---

## 8. Integration plan (high level)

```
[Human / client]
      |
      v
[PromptOS compiler] --IR v2--> [AIGC worker + judgment gates]
      |                              |
      |                              +--> OmniVidz (media)
      |                              +--> RX-LSE (lab twin)
      |                              +--> AutoHouse / tcg (physical product)
      v
[BYOK local runner] ----provider----> [customer-paid model API]
      |
      v
[In-memory control plane stub] --future--> [hosted authorize/settle]
      |
      v
[Webpage + Cloud terminal]  <public face>
[GCP scaffold]              <infra, dry-run default>
```

---

## 9. Implementation roadmap

| Cycle | Window | Deliverable | Gate |
| --- | --- | --- | --- |
| 0 | this PR | Codex + Prime Directive on a docs branch | owner read |
| 1 | next | constellation README index + issue taxonomy labels | no `main` behavior change |
| 2 | next | PromptOS ↔ AIGC IR contract spec + one golden fixture | tests |
| 3 | later | AutoHouse vertical slice compiled through PromptOS | owner review |
| 4 | later | PromptOS clean tree promotion decision | CI green + owner |
| 5 | later | hosted control plane / payments | explicit commercial activation |

---

## 10. DevOps & operations blueprint (as-found)

- PromptOS path-scoped GitHub Actions on feature branches (3.11/3.12). v4.3 head was hosted-CI green.
- GCP master script defaults to dry-run; `--apply` is the live fuse.
- AIGC has Docker, Fly, Render, Procfile — multiple deploy targets, pick one canonical later.
- No constellation-wide CODEOWNERS or shared label set observed in this scan.

---

## 11. Auto-iteration loop specification

Each agent cycle must emit:

1. Scan delta (what changed since last Codex revision)
2. Priority list update
3. Exactly one consequential implementation surface **or** a documented no-op
4. Tests or an explicit "docs-only" label
5. Evidence boundary restated (what is *not* claimed)

This Phase I cycle is **docs-only**. No application code, no merge to `main`, no secrets, no GCP apply, no payments.

---

## 12. Evidence boundary

This Codex does **not** claim:

- a finished OS
- production PromptOS on `main`
- live BYOK against customer keys from this session
- AIGC issue resolution
- professional engineering stamp
- commercial activation

It claims: a first honest map of the Lornt1666 RegenExcalibur constellation as of 2026-08-30, plus a gated plan to evolve it.

Attribution: RegenExcalibur — 1JGM / Justice Gray Maciocha

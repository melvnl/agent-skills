# CLAUDE.md — {{PROJECT_NAME}} · Software Factory Orchestrator

You are the **orchestrator** of this repository's Software Factory. The user talks in plain language ("add X", "Y looks wrong", "continue Z", "review W"). **You** classify the request, discover the relevant documents, select the workflow, and run it. Never ask the user which workflow or file to use; never ask for internal paths. Ask only about decisions that are genuinely theirs (§ 9).

Detailed per-request playbooks live in the **`factory-router`** skill (`.claude/skills/factory-router/SKILL.md`). Load it for any engineering request; this file alone is sufficient if it is unavailable.

---

## 1. Project identity

{{ONE_PARAGRAPH_IDENTITY: what it is, for whom, the core job it does. Evidence-based; mark anything inferred as "(Proposed)".}}
Full vision: `product/PRODUCT_BRIEF.md`.

## 2. Current phase

**{{CURRENT_PHASE}}**
Live state: `tasks/STATUS.md` (resume point). Phase scope and acceptance criteria: `product/ROADMAP.md`. Update this section only when the phase changes.

## 3. Repository map

| Path | What it is | Authority |
|---|---|---|
| `.factory/core/` | Universal standards: `PRINCIPLES`, `ENGINEERING_STANDARDS`, `CODING_STANDARDS`, `TESTING_STANDARDS`, `DEFINITION_OF_DONE`, `AGENT_BEHAVIOR` | How to work (project-agnostic) |
| `.factory/workflows/` | `NEW_FEATURE` (+ `FINTECH_FEATURE` overlay), `PRD_TO_IMPLEMENTATION`, `BUG_FIX`, `PRODUCTION_INCIDENT`, `DATABASE_MIGRATION`, `REFACTORING`, `CODE_REVIEW`, `SECURITY_REVIEW`, `OBSERVABILITY_REVIEW`, `RESUME_WORK`, `NEW_PROJECT` | Process to follow |
| `.factory/templates/` | `PROJECT_BRIEF`, `PRD`, `FEATURE_SPEC`, `TECHNICAL_DESIGN`, `TASK_BREAKDOWN`, `ARCHITECTURE_DECISION_RECORD`, `IMPLEMENTATION_REPORT` | Shape of new documents |
| `product/` | `PRD` (FR/NFR/BR/Q ids), `FEATURES` (F-xx catalog + status), `ROADMAP` (phases, acceptance criteria), `PRODUCT_BRIEF`, `PERSONAS` | What to build, and when |
| `engineering/` | `ARCHITECTURE`, `TECH_STACK`, `DATA_MODEL`, `API_CONTRACTS`, `SECURITY_AND_PRIVACY`, `DEVELOPMENT_GUIDE`, `adr/NNNN-*.md` | How {{PROJECT_NAME}} is built |
| `specs/<F-ID>-<slug>/` | `SPEC.md` + `DESIGN.md` per feature | Feature contract |
| `tasks/` | `STATUS.md` (state), `<F-ID>-<slug>.md` (task breakdowns), `reports/` (implementation reports) | Progress |
{{SOURCE_ROWS: one row per real top-level code/test/infra directory found by inspection, e.g. | `src/` | Application code (layout: `engineering/ARCHITECTURE.md`) | Actual behavior |}}
| `.claude/skills/factory-router/` | Request-routing playbooks | Orchestration |
{{EXISTING_AGENT_FILES_ROW: if AGENTS.md / other agent rule files exist, add a row saying they remain authoritative for what they cover, and link them. Delete this line otherwise.}}

**Rules:** `.factory/` stays project-agnostic, so never put {{PROJECT_NAME}} content there. If a path in this file no longer exists, discover the real one (list the directory), use it, and fix this file.

## 4. Operating principles

1. Follow `.factory/core/AGENT_BEHAVIOR.md`: inspect before modifying; never invent requirements; never silently change acceptance criteria; never disable or weaken tests; never claim results you did not observe; no destructive changes without approval; stay in scope.
2. **Specification before implementation**, scaled to the size of the change (§ 6.2).
3. **Evidence over documents:** code, tests and git history outrank status files. When they disagree, report the discrepancy and fix the docs.
4. **Load only what the request needs** (§ 7). Never read the whole repository "just in case".
5. Respect the current phase and the architectural constraints (§ 8, § 12).

## 5. Session initialization protocol

Run silently at the start of every session, before acting on the first request.

1. **Repository context:** confirm the repo root (the directory containing this file); note the phase (§ 2).
2. **Project state:** read `tasks/STATUS.md`. {{VCS_STEP: "Run `git status` and `git log --oneline -10`." or "This repository is not under version control; note that."}} Glance at the source tree and recent changes. If STATUS contradicts code or tests, trust the evidence and plan to correct STATUS.
3. **Request-specific discovery:** only after classifying the request (§ 6.1), read what § 7 prescribes.

Do not narrate this protocol. Surface only what matters: discrepancies, blockers, or a red build.

## 6. Request handling

Every request goes through: **classify → size → discover → route → execute → close out (§ 10–11).**

### 6.1 Classification and routing

| Type | Signals | Route | Read first |
|---|---|---|---|
| **New functionality** | "add", "support…", "new screen/endpoint" | `.factory/workflows/NEW_FEATURE.md` (+ `.factory/workflows/FINTECH_FEATURE.md` overlay for financial decisions or data) | `product/FEATURES.md` → linked PRD ids → existing `specs/` → ROADMAP phase |
| **Build from a PRD** | "implement this PRD", a large requirements document | `.factory/workflows/PRD_TO_IMPLEMENTATION.md` | The source document → `product/PRD.md`, `product/FEATURES.md` → existing `specs/` |
| **Production incident** | "prod is down", customer-facing errors, wrong data in production | `.factory/workflows/PRODUCTION_INCIDENT.md` (humans act on production), then `BUG_FIX.md` | Alerts, logs by correlation id, recent deploys and config changes |
| **Schema or data migration** | "add a column", "backfill", "rename", "drop" | `.factory/workflows/DATABASE_MIGRATION.md` | `engineering/DATA_MODEL.md` → migrations → table sizes |
| **Bug / incorrect behavior** | "wrong", "broken", "doesn't", error output | Investigate first; `.factory/workflows/BUG_FIX.md` once confirmed | Affected code + tests → feature `SPEC.md` acceptance criteria → PRD business rules |
| **Internal improvement** | "refactor", "clean up", "make faster" (no behavior change) | `.factory/workflows/REFACTORING.md` | Affected code + tests → `engineering/ARCHITECTURE.md` |
| **Code review** | "review", "check", "audit" | `.factory/workflows/CODE_REVIEW.md`; security focus `.factory/workflows/SECURITY_REVIEW.md`; observability focus `.factory/workflows/OBSERVABILITY_REVIEW.md` | Spec/design for the target → code → `engineering/SECURITY_AND_PRIVACY.md` |
| **Resume** | "continue", "where were we", "next" | `.factory/workflows/RESUME_WORK.md`, then the task's own workflow | `tasks/STATUS.md` → active task file → its spec/design |
| **New project** | "start a new project" (not this one) | `.factory/workflows/NEW_PROJECT.md` | `.factory/` only |
| **Investigation** | "why does…", "how does X work" | Lightweight protocol (`factory-router` skill) | Code, tests, relevant `engineering/` section |
| **Architecture question** | "should we use…", trade-offs | Lightweight: analyze and recommend; **no implementation**; propose an ADR if a decision results | `engineering/ARCHITECTURE.md`, `engineering/TECH_STACK.md`, `engineering/adr/`, `product/ROADMAP.md` |
| **Documentation change** | "update the PRD/roadmap/docs" | Lightweight: edit the owning doc, keep cross-references consistent, add a change-log entry | The owning doc (§ 11) + docs that reference it |
| **General question** | "what is…", "explain…" | Answer directly from docs/code, citing files | Only what is needed |

{{ROUTING_EXAMPLES: 3–6 calibration examples using this project's real features and ids, mirroring the table above. Delete this line if the feature catalog is still empty.}}

**Ambiguous intent:** investigate briefly to decide; ask only if evidence cannot settle it. **Composite requests:** split, order (blocking fixes → refactors → features), route each, report per unit. **Missing workflow:** use the closest documented process explicitly, tell the user, and recommend adding one to `.factory/workflows/`.

### 6.2 Sizing

| Size | Criteria | Process |
|---|---|---|
| **Trivial** | Meets `.factory/core/PRINCIPLES.md` § 2 trivial threshold | Do it; run relevant gates; one-paragraph report |
| **Small** | Contained fix/enhancement inside one feature; no data model, contract, security or acceptance-criteria change | Short plan in chat → implement → test → update task file/STATUS |
| **Substantial** | New feature/capability, or any data model, contract, security, architecture or acceptance-criteria change, or several modules | Full lifecycle (§ 6.3) with an approval gate |

### 6.3 Substantial feature lifecycle

1. Restate the request. 2. Search `product/FEATURES.md`, `product/PRD.md`, `specs/` and code for overlap; extend rather than duplicate. 3. Check phase and dependencies (§ 8). 4. List assumptions and open questions. 5. Write/update `specs/<F-ID>-<slug>/SPEC.md` (Given/When/Then, traced to PRD ids). 6. Write `DESIGN.md`; ADR for significant decisions. 7. Write `tasks/<F-ID>-<slug>.md`. 8. **⏸ Present the plan and wait for approval.** 9. Implement task by task, build green. 10. Run all gates (§ 12). 11. Self-review with `.factory/workflows/CODE_REVIEW.md`. 12. Update docs (§ 11) and state (§ 10); write `tasks/reports/<F-ID>-<slug>.md` from `.factory/templates/IMPLEMENTATION_REPORT.md`.

## 7. Context discovery rules

Read in this order, stopping when you have enough: `.factory/core/` (only the relevant standard; `AGENT_BEHAVIOR` always implied) → the routed workflow → templates (only when writing a document) → `product/` (by id/keyword) → `engineering/` (only touched sections) → `specs/` and `tasks/` for the feature → source and tests. Search ids and domain terms before reading. **Never invent paths.**

**Traceability chain:** PRD `FR/NFR/BR` → `FEATURES.md` `F-xx` → `SPEC.md` `AC-n` → `DESIGN.md` → `tasks/` `T-n` → code → tests (cite `AC-n`/`BR-xx`) → `reports/`; decisions → `adr/`.

## 8. Phase and architecture gate

- Find the feature's phase in `product/FEATURES.md` and `product/ROADMAP.md`. Later phase or unfinished dependencies → stop and offer: spec now/build later, a current-phase slice, or a roadmap change (owner approval).
- No new technologies, services, dependencies or abstractions without a requirement; anything not in `engineering/TECH_STACK.md` needs justification and an update there; significant changes need an ADR.
{{PHASE_CONSTRAINTS: project-specific phase rules, e.g. "Phase 1 must not depend on X". Delete if none are known yet.}}

## 9. Human approval boundaries

| Requires explicit owner approval | Proceed without asking |
|---|---|
| Substantial plan before implementation (§ 6.3 step 8) | Trivial/small changes within approved scope |
| New or changed requirements, acceptance criteria, roadmap/phase scope | Reading, searching, running tests/builds/linters |
| ADR acceptance; data migrations; contract, auth, permission or privacy changes | Implementation details consistent with the approved design |
| New dependencies or infrastructure | Updating task files, STATUS and docs to reflect actual work |
| Destructive actions: deleting files/data, schema drops, mass renames, commits/pushes, history rewrites | Creating specs/designs as **drafts** for review |
| Resolving open questions in `product/PRD.md` | Choosing between equivalent internal approaches (document the choice) |

## 10. Project state and continuity

- **`tasks/STATUS.md` is the single state file**: snapshot (phase, active feature, current task, last verified build), implemented capabilities, next actions, blockers, recent decisions, tech debt. Link out; never copy specs.
- Task progress lives in `tasks/<F-ID>-<slug>.md`; feature status in `product/FEATURES.md`.
- Update STATUS at the end of every session that changed anything. Record verification (date, command, result) only for commands actually run.
- Authority order: version control and code > tests > approved specs > STATUS.

## 11. Documentation maintenance

| Change | Update |
|---|---|
| Requirement / scope | `product/PRD.md` (+ change log), `product/FEATURES.md`, affected `SPEC.md` |
| Phase or ordering | `product/ROADMAP.md`, `product/FEATURES.md`, § 2 of this file |
| Architecture / module boundaries | `engineering/ARCHITECTURE.md` + new ADR |
| Entities, fields, storage schema | `engineering/DATA_MODEL.md` |
| Service/API contracts | `engineering/API_CONTRACTS.md` |
| Auth, isolation, data handling, secrets | `engineering/SECURITY_AND_PRIVACY.md` |
| Dependencies / tools | `engineering/TECH_STACK.md` |
| Commands, setup, conventions | `engineering/DEVELOPMENT_GUIDE.md` + § 12 here |
| Behavior differs from spec | Fix the code, or amend the spec with approval (never silently) |

Accepted ADRs are immutable: supersede them with a new ADR.

## 12. Development and quality

**Stack** (details: `engineering/TECH_STACK.md`): {{STACK_ONE_LINE: detected languages, frameworks, data stores, test tools, package manager, with versions where known.}}

**Commands** (`engineering/DEVELOPMENT_GUIDE.md`): {{COMMANDS: the real install/dev/build/lint/typecheck/test/e2e commands found in manifests. Mark any that do not exist yet as "(planned)". Name the single aggregate gate if one exists.}}

**Architectural constraints** (non-negotiable unless changed by ADR):
{{CONSTRAINTS: numbered list of constraints observed in the code (layering, data access boundaries, isolation, purity rules), each labeled Confirmed (seen in code) or Proposed (needs owner confirmation). Keep to what evidence supports.}}

**Conventions** (details: `engineering/DEVELOPMENT_GUIDE.md`): {{CONVENTIONS: naming, domain terms, requirement-id citation in tests/code, decision labels (Confirmed / Proposed / Open question / Future consideration), commit policy ("ask the owner before committing or pushing").}}

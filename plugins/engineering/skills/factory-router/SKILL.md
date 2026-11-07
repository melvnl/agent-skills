---
name: factory-router
description: Classifies any engineering request in a repository that uses the .factory Software Factory (feature, bug, refactor, review, resume, PRD, migration, incident, new project, investigation, architecture, docs, question), sizes it, and routes it to the right workflow and approval gates. The entry point for spec-driven development. Use at the start of every development request in such a repository, even when no workflow or file is named. Shortcut: /factory-router <request>.
---

# Factory Router

Turns a plain-language request into the right Software Factory process. **Project-agnostic:** project paths, phase, and constraints come from the project's entry point (root `CLAUDE.md`), which wins on any project-specific detail. Standards and workflows come from `.factory/`. This skill only routes; it does not restate them.

## 0. Preconditions (once per session)

The session-initialization protocol in the project entry point must have run: phase known, state file read, `git status` checked (or "not a git repo" noted). If it has not, run it now.

## 1. Classify

Choose exactly one primary type per unit of work, based on what the user wants as an outcome, not on the verbs they use.

| Type | Outcome the user wants | Route |
|---|---|---|
| FEATURE | New or extended user-visible capability | `.factory/workflows/NEW_FEATURE.md` (+ `.factory/workflows/FINTECH_FEATURE.md` overlay when it changes financial decisions or data) |
| PRD | Build from a large requirements document | `.factory/workflows/PRD_TO_IMPLEMENTATION.md` → `NEW_FEATURE` per feature |
| BUG | Actual behavior ≠ specified/expected behavior | Investigate → `.factory/workflows/BUG_FIX.md` if confirmed |
| INCIDENT | Production is broken, degraded, wrong, or exposing data **now** | `.factory/workflows/PRODUCTION_INCIDENT.md` (mitigation by humans first), then `BUG_FIX` |
| MIGRATION | Schema change, data migration, or backfill on shared data | `.factory/workflows/DATABASE_MIGRATION.md` |
| REFACTOR | Better internals, same observable behavior | `.factory/workflows/REFACTORING.md` |
| REVIEW | An assessment of existing code or a change | `.factory/workflows/CODE_REVIEW.md`; security focus → `.factory/workflows/SECURITY_REVIEW.md`; observability focus → `.factory/workflows/OBSERVABILITY_REVIEW.md` |
| RESUME | Continue previous or unfinished work | `.factory/workflows/RESUME_WORK.md` → the task's own workflow |
| NEW_PROJECT | Bootstrap a different project | `.factory/workflows/NEW_PROJECT.md` |
| INVESTIGATE | Understand how or why something behaves | § 4.1 (lightweight) |
| ARCHITECTURE | Decide or evaluate a technical direction | § 4.2 (lightweight; no implementation) |
| DOCS | Change documentation or requirements text | § 4.3 (lightweight) |
| QUESTION | An explanation | § 4.4 (direct answer) |

Disambiguation rules:
- "X is slow": measure before deciding. A regression against a documented NFR is a BUG; an improvement with no behavior change is a REFACTOR; new behavior (e.g. caching that changes freshness) is a FEATURE.
- "X is wrong": INVESTIGATE first. If the code violates the spec, it is a BUG. If the code matches the spec but the spec is wrong, it is DOCS, a requirement change that needs approval, then a FEATURE or BUG for the code.
- "Continue X": RESUME scoped to X, even if X is a feature.
- "Should we…": ARCHITECTURE. Never implement on the back of a question.
- "Production is down / customers see errors / data looks wrong in prod": INCIDENT first, even if it is also a bug. Stabilize, then fix.
- "Implement this PRD / build from this spec document": PRD, when the document spans several features; a single small feature is FEATURE.
- A FEATURE or BUG that needs a schema change runs `DATABASE_MIGRATION` for that part.
- Composite requests: split into units, order them (blocking bugs → refactors → features → docs), route each, and report per unit.

If a routed workflow file is missing: look for an equivalent in `.factory/workflows/`. If there is none, tell the user about the gap, use the closest documented process explicitly, and recommend adding the workflow. Never improvise a process silently.

## 2. Size

| Size | Test | Process weight |
|---|---|---|
| Trivial | Meets `.factory/core/PRINCIPLES.md` § 2 trivial threshold | Do → verify → 1-paragraph report |
| Small | Inside one existing feature; no change to data model, contracts, security, or acceptance criteria | Short plan in chat → do → verify → update task/state files |
| Substantial | Anything else | Full workflow with approval gate before implementation |

Start light; escalate the moment a heavier criterion appears, and tell the user you are escalating.

## 3. Discover (minimum necessary context)

1. Extract keywords: domain nouns, feature names, ids.
2. Search the project's feature catalog, requirements, specs, and task files for them (grep or glob; paths come from the entry point's repository map).
3. Read only the matching sections, then the workflow file, then templates if you are writing a document.
4. Read code and tests for anything that already exists. They define actual behavior.
5. Record what you found: an existing feature id, an existing spec, related requirements, phase, dependencies, and gaps.

Duplicate check (FEATURE): if an existing feature or spec covers the request, **extend it** (new requirement or acceptance-criteria rows plus a change-log entry) instead of creating a parallel spec.

## 4. Lightweight protocols (no dedicated factory workflow exists)

These are interim procedures for request types that `.factory/workflows/` does not cover. They are deliberately minimal; promote them to full workflow files if they grow.

### 4.1 INVESTIGATE
1. State the question precisely.
2. Gather evidence: code paths, tests, docs, and reproductions, running things where possible.
3. Answer with evidence (`file:line`, command output) and a confidence level.
4. If a defect is found, offer to switch to BUG. If a design gap is found, offer FEATURE or ARCHITECTURE. Change nothing without being asked.

### 4.2 ARCHITECTURE
1. Restate the decision and why it is being asked now.
2. Read the architecture doc, relevant ADRs, tech stack, and roadmap phase.
3. Compare 2–3 options against the project's requirements, constraints, and existing ADRs: pros, cons, cost, reversibility, and phase fit.
4. Recommend one option, with what would change the recommendation.
5. If the user agrees and the decision is significant, draft an ADR (status **Proposed**) from `.factory/templates/ARCHITECTURE_DECISION_RECORD.md`. **No implementation.**

### 4.3 DOCS
1. Identify the owning document (the entry point's documentation-maintenance table).
2. If the change alters requirements, acceptance criteria, scope, phase, or an accepted decision, get approval first.
3. Edit the owner, update cross-references (ids, feature catalog, specs) so nothing contradicts, and add a change-log entry where the document has one.
4. Report exactly which files changed.

### 4.4 QUESTION
Answer directly and concisely from the docs and code, citing files. Do not start a workflow or modify files.

## 5. Gates that always apply

- **Phase gate:** check the feature's phase in the roadmap or feature catalog. If it belongs to a later phase or depends on unfinished work, explain the conflict and offer: spec now and build later, a current-phase slice, or a roadmap change (approval needed).
- **Approval gate (substantial work):** present the summary, scope and non-goals, acceptance criteria, affected components and data, risks, open questions, and the task list. Then **stop and wait**.
- **Approval-required actions:** follow the entry point's approval table and `.factory/core/AGENT_BEHAVIOR.md` H6.
- **Verification:** run the project's quality gates and report actual results. Commands that do not exist yet are reported as such, never as passed.

## 6. Close-out checklist (every unit of work that changed something)

- [ ] Docs updated per the entry point's maintenance table, and only those that actually changed.
- [ ] Task file and feature status updated.
- [ ] State file updated: active feature and task, next action, blockers, and last verification (date, command, result).
- [ ] Report given: inline for trivial/small work, or the `.factory/templates/IMPLEMENTATION_REPORT.md` file for substantial work.
- [ ] Assumptions, limitations, and open questions stated.

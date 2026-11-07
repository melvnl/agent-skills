# Populating project documents from evidence

How factory-init fills each project file. The rule everywhere: **write what the repository proves, label what you infer, and ask about what only the owner knows.** Never invent requirements, users, targets, or decisions.

## Decision labels (use them on every non-obvious statement)

| Label | Meaning | Example source |
|---|---|---|
| **Confirmed** | Seen in code, config, tests, or stated by the owner | `package.json` lists `next@16` |
| **Proposed** | Your inference; owner should confirm | "Layered as routes → services → repo" from folder names |
| **Open question** | Unknown; needs the owner | Target users, roadmap phases |
| **Future consideration** | Explicitly deferred | A TODO for a later integration |

## Evidence → document map

| File | Fill from | Mark as Open question when |
|---|---|---|
| `product/PRODUCT_BRIEF.md` (template `PROJECT_BRIEF`) | README, package description, landing copy, owner interview | Vision, goals, non-goals not stated anywhere |
| `product/PERSONAS.md` | Owner interview; README audience statements | Always, unless the owner described users |
| `product/PRD.md` (template `PRD`) | **Existing behavior** becomes FR rows marked "Implemented (Confirmed)", derived from routes, screens, endpoints and tests. Measured limits become NFRs only if enforced in code or tests. | New requirements: never add them; list ideas as Open questions in § Open questions |
| `product/FEATURES.md` | Group the FRs into F-xx features, each with linked FR ids, phase, and status (✅ for implemented, ⬜ for not started) | Phase assignment for anything not built |
| `product/ROADMAP.md` | Phase 0/1 = what exists today (✅). Later phases only from the owner or explicit TODO/issue evidence | Everything beyond the current state |
| `engineering/TECH_STACK.md` | Manifests, lockfiles, config files, CI; exact versions; rationale only if documented, else "(rationale not recorded)" | Why a technology was chosen |
| `engineering/ARCHITECTURE.md` | Directory layout, entry points, import direction, runtime topology (Docker/compose, serverless config, CI deploy); Mermaid context diagram | Intended boundaries that the code does not enforce |
| `engineering/DATA_MODEL.md` | ORM schemas, migrations, SQL, type definitions, validation schemas | Ownership/retention rules not encoded anywhere |
| `engineering/API_CONTRACTS.md` | Route handlers, OpenAPI/GraphQL schemas, RPC definitions, repository/service interfaces | Versioning and compatibility policy |
| `engineering/SECURITY_AND_PRIVACY.md` | Auth middleware, permission checks, env var names in `.env.example` (never values), secret handling, CSP/headers | Data classification, retention, compliance needs |
| `engineering/DEVELOPMENT_GUIDE.md` | Real commands from scripts/Makefile; prerequisites from engines/version files; lint/format/type configs → conventions; map each `.factory/core/DEFINITION_OF_DONE.md` gate to a command, "(planned)" if absent | — |
| `engineering/adr/0001-initial-architecture.md` | Record the **existing** foundational choices as status *Accepted (retroactive)*, citing evidence | Choices the owner may want to revisit (list them as open) |
| `tasks/STATUS.md` | Snapshot table, implemented capabilities (from FEATURES), next actions, blockers, and the verification you actually ran today with its result | — |
| `specs/` | Create the directory with a `README.md` explaining the `<F-ID>-<slug>/SPEC.md + DESIGN.md` convention. Do **not** back-fill specs for existing features unless asked. | — |

## Owner interview (keep it to one round, at most 4 questions)

Ask only what changes the documents and cannot be read from the repo. Typical set:
1. One-sentence purpose and who uses it.
2. Current phase/milestone and what "done" means for it.
3. Any hard constraints (platform, compliance, data sensitivity, budget).
4. Anything in the code that is legacy, being replaced, or off-limits.

If the owner prefers not to answer, proceed with Open-question markers rather than guesses.

## Project-specific engineering standards

`.factory/core/` stays generic. Project-specific standards go in `engineering/DEVELOPMENT_GUIDE.md` (conventions and gates) and § 12 of `CLAUDE.md` (stack, commands, constraints). Derive them from:
- Strictness flags (`tsconfig` `strict`, mypy/pyright settings, `-Werror`).
- Lint and format configs (which rules are errors).
- Test layout (unit vs integration vs E2E dirs, naming), coverage thresholds in config.
- Existing patterns repeated across the codebase (e.g. all DB access through one module): record as **Proposed** constraint unless a linter or test enforces it (then **Confirmed**).

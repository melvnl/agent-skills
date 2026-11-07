---
name: factory-init
description: Bootstraps or verifies the .factory Software Factory in a repository: detects the stack, installs the project-agnostic factory, populates product and engineering docs and tasks/STATUS.md from evidence, creates or merges CLAUDE.md without overwriting existing files, and verifies files and cross-references. Run as /factory-init [--verify] to adopt spec-driven development in a repository.
disable-model-invocation: true
---

# Factory Init

Sets up the Software Factory in the current repository. Companion of `factory-router`: **factory-init installs the factory, factory-router runs requests through it.** The factory itself is bundled in `assets/` so this skill works in any repository.

| Bundled file | Purpose |
|---|---|
| `assets/factory/` | Canonical, project-agnostic `.factory/` (core, workflows, templates, README) |
| `assets/factory-router.SKILL.md` | Installed as `.claude/skills/factory-router/SKILL.md` |
| `scripts/detect_stack.sh [root]` | Read-only repository inventory (VCS, manifests, deps, scripts, configs, docs) |
| `scripts/install_factory.sh [--dry-run] [--with-router] [root]` | Copies the bundled factory, **no-clobber**: CREATE / SKIP (identical) / CONFLICT (differs, untouched); exit 3 on conflicts |
| `scripts/verify_factory.sh [--relaxed] [--project-name N] [root]` | Required files, CLAUDE.md wiring, unresolved references, leftover `{{PLACEHOLDERS}}`, project terms leaking into `.factory/`, drift vs. bundle; exit 1 on any FAIL |
| `references/CLAUDE_TEMPLATE.md` | Skeleton for the orchestrator `CLAUDE.md` (`{{PLACEHOLDER: instructions}}` slots) |
| `references/POPULATION_GUIDE.md` | What evidence fills which project doc, decision labels, owner-interview questions |

Run scripts by absolute path (`<this skill dir>/scripts/...`) from the target repo root.

## Hard rules

1. **Never overwrite or delete an existing file without explicit approval.** Existing file → read it, then either leave it, or propose a specific merge (show the diff) and wait. This includes `CLAUDE.md`, `AGENTS.md`, `README.md`, and any doc under `product/`, `engineering/`, `tasks/`.
2. **`.factory/` stays project-agnostic.** Install it verbatim from `assets/factory/`; put every project fact in `CLAUDE.md`, `product/`, `engineering/`, `tasks/`.
3. **Evidence only.** Document what the repository proves; label inferences *Proposed* and unknowns *Open question* (`references/POPULATION_GUIDE.md`). Never invent requirements, users, phases, or decisions.
4. **Report what you observed.** Verification results are the actual script/command output, never assumed.
5. No commits, pushes, `git init`, dependency installs, or app scaffolding. Those are separate, approved steps (`.factory/workflows/NEW_PROJECT.md` Stage E).

## Mode selection

- `.factory/` **missing** → bootstrap (§ 1–6).
- `.factory/` **present**, or the user passed `--verify` → do not bootstrap. Run § 6 (verify) only, report drift against the bundle as information, and offer targeted fixes (each needing approval if it changes an existing file). If `.factory/` is partial, offer to add only the missing files (`install_factory.sh` does exactly that; it never touches existing ones).

## 1. Inspect (read-only)

1. Run `scripts/detect_stack.sh`. Then read what it points to: README, existing agent files (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, Copilot instructions), `docs/`, main entry points, a few representative source and test files, CI workflows, schema/migration files.
2. Determine, with evidence for each: languages and versions; frameworks; package manager; data stores/ORM; test levels and runners; lint/format/type tooling; build/deploy targets; monorepo layout; real commands (install, dev, build, lint, typecheck, test, e2e, aggregate gate).
3. Inventory **collisions**: every target path from § 3 that already exists. Run `scripts/install_factory.sh --dry-run --with-router` to list factory-file outcomes.
4. If the repo is empty or nearly so (no source, no manifest), say so: this is a new project, so follow `assets/factory/workflows/NEW_PROJECT.md` Stage A–D (interview first) instead of deriving docs from code.

## 2. Plan and get approval (⏸ gate)

Present, concisely:
- **Detected stack** (one table: area → technology/version → evidence file).
- **Files to create** (grouped: `.factory/`, router skill, `product/`, `engineering/`, `specs/`, `tasks/`, `CLAUDE.md`).
- **Collisions** and the proposed handling for each: *keep as is*, *merge (append section)*, or *rename the new file* (e.g. existing `docs/ARCHITECTURE.md` → keep it and link it from `engineering/ARCHITECTURE.md` instead of duplicating). Default is keep.
- **Owner questions** (max 4, from `references/POPULATION_GUIDE.md` § Owner interview), only for facts the repo cannot answer.
- Notes: `.factory/` and `.claude/` may be git-ignored in this repo; mention it if `.gitignore` says so, and do not change `.gitignore` unasked.

Use AskUserQuestion for the collision choices and owner questions when there are any. Stop until the owner approves. Without answers, proceed with *Open question* markers rather than guesses.

## 3. Install the factory

Run `scripts/install_factory.sh --with-router` (omit `--with-router` if the owner declined it). Exit 3 means conflicts: leave those files untouched and list them in the final report.

## 4. Populate project documents

Create only files that do not exist (or that the owner approved merging). Use the `.factory/templates/` shapes and `references/POPULATION_GUIDE.md`:

```text
product/   PRODUCT_BRIEF.md  PRD.md  PERSONAS.md  ROADMAP.md  FEATURES.md
engineering/   ARCHITECTURE.md  TECH_STACK.md  DATA_MODEL.md  API_CONTRACTS.md
               SECURITY_AND_PRIVACY.md  DEVELOPMENT_GUIDE.md  adr/0001-initial-architecture.md
specs/README.md           (convention only; no back-filled specs)
tasks/STATUS.md  tasks/reports/   (reports dir may stay empty)
```

- Scale to the codebase: a small repo gets short docs. A doc with nothing to say yet holds its headings plus an *Open question* line, not filler.
- Not applicable (e.g. no API, no persistence): keep the file with one sentence saying so and why, so references stay valid.
- If the project already keeps equivalent docs elsewhere, **link** to them rather than copying, and record the mapping in `CLAUDE.md` § 3 (the factory allows adapted layouts; verification then uses `--relaxed`).
- Use stable ids from the start: `FR-n`, `NFR-n`, `BR-n`, `Q-n` in the PRD; `F-nn` in FEATURES; ADRs `NNNN-slug.md`.
- Project-specific engineering standards (strictness, lint severity, test layout, enforced boundaries) go in `DEVELOPMENT_GUIDE.md` and `CLAUDE.md` § 12, never in `.factory/core/`.

## 5. Create or merge the root CLAUDE.md

- **No `CLAUDE.md`:** write it from `references/CLAUDE_TEMPLATE.md`, replacing every `{{…}}` slot with project facts (or deleting slots marked deletable). Keep it an orchestrator: link to `.factory/` and project docs; do not copy their content.
- **`CLAUDE.md` exists:** do not replace it. Read it fully and propose a merge that preserves all existing content and adds the missing orchestrator parts (role, repository map rows for `.factory/` and docs, session protocol, routing table, sizing, phase gate, approval table, state and doc-maintenance rules). Show the diff, wait for approval, then apply.
- **`AGENTS.md` or other agent rule files exist:** keep them; reference them from `CLAUDE.md` § 3 as still authoritative for their scope.
- `tasks/STATUS.md` snapshot: phase, active feature (none), last verification = what you ran in § 6 today.

## 6. Verify

1. Run `scripts/verify_factory.sh --project-name "<project name>"` (add `--relaxed` only if `CLAUDE.md` documents an adapted layout).
2. Fix every **FAIL** you introduced (missing file, missing wiring, broken path, leftover `{{…}}`), then re-run until it reports 0 FAIL. Fixes to pre-existing files still need approval.
3. Read each **WARN**: references to planned or not-yet-written paths are fine if the doc says "planned"; otherwise fix.
4. Also run the project's own existing gates **only if they are read-only and cheap** (lint, typecheck) to record a truthful "last verification" in STATUS; never install dependencies to do so. If you ran nothing, STATUS says "not yet verified".

## 7. Report

Keep it short:
- Stack detected (one line).
- Created files (count per directory), merged files, skipped/conflicting files (each by path, with why).
- Verification: the `summary:` line from `verify_factory.sh` and any remaining WARNs worth attention.
- Open questions recorded and where (PRD `Q-n` ids).
- Next step: "Ask for anything in plain language; the `factory-router` skill will route it" plus, if relevant, the first suggested task (e.g. answer the open questions, or confirm the Proposed constraints).

## Maintaining this skill

`assets/` is a snapshot of the reference factory. When the reference `.factory/` or `factory-router` skill improves, refresh the snapshot (copy the files over) so new installs get the change; `verify_factory.sh` reports drift between a repo's `.factory/` and the snapshot.

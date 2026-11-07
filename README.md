# melvin-skills

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/agent-skills-banner-dark.svg">
  <img src="docs/assets/agent-skills-banner-light.svg" alt="agent-skills: engineering skills, agents and guardrails for Claude Code" width="100%">
</picture>

**Portable engineering capabilities for Claude Code: spec-driven workflows, backend and fintech expertise, observability by default, and deterministic guardrails.**

Skills encode *how* senior engineers do the work, agents define *who* does it and with what authority, hooks enforce *what is allowed*, and Software Factory workflows decide *in what order*, with human approval at every gate. Everything is packaged as Claude Code plugins in one marketplace, so each project installs only the profiles it needs.

```
  DEFINE            PLAN             BUILD             VERIFY            REVIEW             SHIP
 ┌────────┐      ┌────────┐       ┌────────┐       ┌────────┐       ┌─────────┐       ┌────────┐
 │  PRD   │ ───▶ │ Design │ ───▶  │  Loop  │ ───▶  │ Tests  │ ───▶  │ Review  │ ───▶  │Release │
 │Analysis│      │ Tasks  │       │TDD+Logs│       │  QA    │       │Sec/Obs/ │       │Rollback│
 │  Specs │      │  ADRs  │       │        │       │ Trace  │       │ Fintech │       │Approval│
 └────────┘      └────────┘       └────────┘       └────────┘       └─────────┘       └────────┘
 prd-analysis    planning-and-    loop-engineering  qa-engineer      code-reviewer     human
 specification-  task-breakdown   test-driven-dev.  requirement-     observability-    approval
 decomposition   solution-        structured-       traceability     engineer          gate
                 architect        logging-...                        security-auditor
        └──────────────── routed by factory-router, guarded by engineering-guardrails ────────────────┘
```

Inspired by [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (lifecycle-ordered, process-heavy skills) and [mattpocock/skills](https://github.com/mattpocock/skills) (small, composable skills).

---

## What's inside

| | Count | Where |
|---|---|---|
| Plugins (installable profiles) | 7 | `plugins/<profile>/` |
| Skills | 41 | `plugins/<profile>/skills/` |
| Specialist agents | 11 | `plugins/<profile>/agents/` |
| Guardrail hooks | 18 (92 unit tests) | `plugins/guardrails/` |
| Software Factory workflows | 11 (+ fintech overlay) | `plugins/engineering/skills/factory-init/assets/factory/workflows/` |
| Eval cases (native `claude plugin eval`) | 39 | `plugins/<profile>/evals/` |

---

## Quick start

**1. Install with the CLI** (wraps `claude plugin` commands; dependencies install automatically):

```bash
git clone <repo-url> ~/dev/agent-skills
cd ~/dev/agent-skills
scripts/agent-skills profiles                                    # list profiles
scripts/agent-skills install --profile core --profile guardrails # every project (user scope)
scripts/agent-skills doctor                                      # verify the setup
```

**2. Per project**, install only what it needs (writes the project's `.claude/settings.json`, which you can commit):

```bash
cd ~/work/eligibility-service
~/dev/agent-skills/scripts/agent-skills install --profile fintech --profile guardrails --scope project
```

**3. Adopt the Software Factory** in a repository by running `/factory-init` inside it. From then on, ask in plain language; `factory-router` classifies the request and runs the right workflow.

**New machine:** `scripts/bootstrap.sh --repo <repo-url> --profile core --profile guardrails` clones, installs, and runs `doctor`.

**Manual install:** `claude plugin marketplace add <path-or-repo>`, then `claude plugin install <plugin>@melvin-skills`.

**Updating:** a local checkout is read in place: `git pull`, then start a new session or run `/reload-plugins`. For a GitHub-hosted marketplace: bump versions and run `scripts/agent-skills update` ([release strategy](docs/release-strategy.md)).

---

## Plugins and profiles

| Profile | Plugin | What it gives you | Depends on |
|---|---|---|---|
| `core` | [spec-driven-engineering](plugins/engineering/README.md) | Software Factory, product discovery, PRD analysis, specs, planning, loop and context engineering, TDD, debugging, git discipline | none |
| `observability` | [observability](plugins/observability/README.md) | Structured logging, correlation and tracing, PII-safe logging, observability design and review | none |
| `security` | [application-security](plugins/security/README.md) | Authorization and IDOR, injection, SSRF, webhook verification, secrets | none |
| `backend` | [python-backend](plugins/backend/README.md) | Python, Django, FastAPI, API and database design, migrations, MySQL/Aurora, Redis, distributed systems, SQS/SNS, performance | spec-driven-engineering, observability |
| `fintech` | [fintech-engineering](plugins/fintech/README.md) | Credit scoring and eligibility, risk decisions, data integrity, decimal money, authorization, auditability, reliability | python-backend, observability, application-security |
| `guardrails` | [engineering-guardrails](plugins/guardrails/README.md) | 18 deterministic hooks | none |
| `writing` | [technical-writing](plugins/writing/README.md) | Engineering blog pipeline | none |
| `all` | every plugin above | | |

Suggested combinations: blog repo → `writing`; fintech backend → `fintech` + `guardrails`; other Python backends → `backend` + `guardrails`; experiments → `core`.

---

## How it fits together

| Type | Answers | Example |
|---|---|---|
| **Skill** | *How* to do a task | `structured-logging-and-instrumentation` decides which events deserve a log entry |
| **Agent** | *Who* does it, with what authority | `observability-engineer` reviews instrumentation, read-only |
| **Hook** | *What* is allowed, deterministically | `detect-sensitive-logging` flags a log call containing `authorization` |
| **Workflow** | *In what order*, with which approvals | `PRD_TO_IMPLEMENTATION` stops for your decisions on contradictions |

A typical PRD-driven feature:

1. `factory-router` classifies "implement this PRD" and starts `PRD_TO_IMPLEMENTATION`.
2. `prd-analysis` preserves the source and lists contradictions, ambiguities, and missing NFRs. **You resolve them.**
3. `specification-decomposition` and `acceptance-criteria-engineering` produce stable ids and atomic specs. **You approve them.**
4. `solution-architect` writes the design, including failure scenarios and the observability plan.
5. `planning-and-task-breakdown` produces ordered tasks; `backend-engineer` implements each with `loop-engineering`, `test-driven-development`, and instrumentation.
6. `qa-engineer` verifies independently; `code-reviewer`, `observability-engineer`, `security-auditor`, and the fintech reviewers review. The implementer never approves its own work.
7. Release notes and rollback considerations; **you approve deployment.**

State lives in the project (`tasks/STATUS.md`, task files, specs), not in the conversation, so any session can resume.

---

## Software Factory workflows

Installed into a project as `.factory/` by `/factory-init`; selected per request by `factory-router`.

| Workflow | Use when | Key gates |
|---|---|---|
| `NEW_FEATURE` | New or extended capability | spec approval, design approval, implementation loop with stop conditions, independent review |
| `FINTECH_FEATURE` (overlay) | The feature changes credit, eligibility, risk, limits or money | policy traceability, owner-approved fallbacks, golden-set checks, maker-checker activation, distribution canary |
| `PRD_TO_IMPLEMENTATION` | Building from a large requirements document | analysis resolved, specs approved, verification, deployment approval |
| `BUG_FIX` | Behavior differs from the spec | evidence-based investigation, regression test fails first |
| `PRODUCTION_INCIDENT` | Production is broken, degraded or exposing data | humans perform every production action |
| `DATABASE_MIGRATION` | Schema changes, backfills | expand-migrate-contract, rehearsal evidence, approval for destructive steps |
| `REFACTORING` | Better internals, same behavior | zero test-expectation changes |
| `CODE_REVIEW` | Any change | reviewer is not the implementer; observability and data-integrity checklist |
| `SECURITY_REVIEW` | Endpoints, integrations, auth, secrets | exploit scenarios with proving tests |
| `OBSERVABILITY_REVIEW` | Backend changes | correlation at every boundary, no sensitive data in logs |
| `RESUME_WORK`, `NEW_PROJECT` | Continuing work; bootstrapping | state from files, not memory |

---

## Observability by default

Every backend change is evaluated for instrumentation, and the goal is useful observability, not maximum log volume:

- **Decide before logging.** A 15-event, 7-question framework: is it diagnostic, not already observable, needed to correlate a failure, worth its volume, free of sensitive data?
- **Reuse what exists.** The project's logger, wrapper and correlation mechanism are inspected first. Internal logger APIs are never invented.
- **Correlate across boundaries.** Request, correlation and trace ids survive HTTP, SQS/SNS, workers and thread pools, with the fewest identifiers possible.
- **Keep data safe.** Secrets never; personal and financial identifiers only as approved references or keyed pseudonyms; allowlisted fields instead of payloads.
- **Prove it.** The formatter actually emits the fields, correlation appears in captured records, and a sentinel test shows sensitive values are absent.
- **Logs are not audit records.** Decisions and financial changes get durable, append-only records (`financial-auditability`).

---

## All 41 skills

### spec-driven-engineering: define, plan, build, verify

| Skill | What it does | Use when |
|---|---|---|
| [factory-init](plugins/engineering/skills/factory-init/SKILL.md) | Installs or verifies the `.factory/` Software Factory, populates project docs from evidence, merges `CLAUDE.md` without overwriting | Adopting spec-driven development in a repo (`/factory-init [--verify]`) |
| [factory-router](plugins/engineering/skills/factory-router/SKILL.md) | Classifies, sizes and routes every request to the right workflow and gates | Any development request in a factory repo |
| [product-discovery](plugins/engineering/skills/product-discovery/SKILL.md) | One-question-at-a-time interview that turns an idea or an undocumented request into an owner-approved brief, PRD and roadmap, traced to an interview record and self-checked with `prd-analysis` | Starting from an idea, or there is no PRD |
| [prd-analysis](plugins/engineering/skills/prd-analysis/SKILL.md) | Extracts requirements with source references; surfaces contradictions, ambiguities, duplicates, missing NFRs, AI artifacts | A PRD or requirements document arrives |
| [specification-decomposition](plugins/engineering/skills/specification-decomposition/SKILL.md) | Stable ids, domain groups, feature catalog, atomic feature specs | After analysis, to cut buildable features |
| [acceptance-criteria-engineering](plugins/engineering/skills/acceptance-criteria-engineering/SKILL.md) | Given/When/Then criteria covering a 12-category matrix (boundaries, permissions, failures, idempotency, time, money, audit...) | Writing or reviewing "done" |
| [requirement-traceability](plugins/engineering/skills/requirement-traceability/SKILL.md) | Keeps PRD → feature → AC → task → code → test traced, with a deterministic `trace_check.py` | Before closing a feature, or when specs change |
| [planning-and-task-breakdown](plugins/engineering/skills/planning-and-task-breakdown/SKILL.md) | Walking skeleton first, vertical slices, tasks with tests, instrumentation and done-when | An approved spec needs implementation tasks |
| [loop-engineering](plugins/engineering/skills/loop-engineering/SKILL.md) | Implement → instrument → test → diagnose → fix → verify → checkpoint, with stop conditions | Implementing a task list, autonomous multi-step work |
| [context-engineering](plugins/engineering/skills/context-engineering/SKILL.md) | Targeted reading, bounded output, state in files, compaction-proof handoffs | Long tasks, large codebases or documents |
| [test-driven-development](plugins/engineering/skills/test-driven-development/SKILL.md) | Red-green-refactor from the acceptance criteria, pytest/Django/FastAPI patterns | Implementing behavior or fixing bugs |
| [debugging-and-error-recovery](plugins/engineering/skills/debugging-and-error-recovery/SKILL.md) | Reproduce, minimize, one hypothesis at a time, bisect, root cause, safe recovery | Bugs, failing tests, non-converging fixes |
| [git-workflow](plugins/engineering/skills/git-workflow/SKILL.md) | Small Conventional Commits, explicit staging, reviewed diffs, no history rewriting without approval | Committing, branching, PRs |

### observability

| Skill | What it does | Use when |
|---|---|---|
| [structured-logging-and-instrumentation](plugins/observability/skills/structured-logging-and-instrumentation/SKILL.md) | Decides what deserves a log; structured, correlated, PII-safe logs with the project's own logger | Any backend implementation or change |
| [distributed-tracing-and-correlation](plugins/observability/skills/distributed-tracing-and-correlation/SKILL.md) | Request, correlation and trace context across HTTP, SQS/SNS, workers and async code | A change crosses a service, queue, thread or task boundary |
| [logging-security-and-redaction](plugins/observability/skills/logging-security-and-redaction/SKILL.md) | Four-tier data classification; allowlists, keyed pseudonyms, masking, sentinel tests | Adding or reviewing log statements and error handling |
| [observability-engineering](plugins/observability/skills/observability-engineering/SKILL.md) | Question-driven logs/metrics/traces design, cardinality, SLO-based alerting, the observability plan | Designing a feature or service, defining alerts |
| [observability-code-review](plugins/observability/skills/observability-code-review/SKILL.md) | Reviews a diff for gaps *and* over-instrumentation, correlation loss, sensitive data, unbounded labels | Reviewing backend changes |

### python-backend

| Skill | What it does | Use when |
|---|---|---|
| [python-backend-engineering](plugins/backend/skills/python-backend-engineering/SKILL.md) | Version-safe Python, timeouts, aware datetimes, Decimal money, exception chaining | Any Python backend code |
| [django-engineering](plugins/backend/skills/django-engineering/SKILL.md) | Service-layer rules, constraints, N+1-free querysets, `on_commit` side effects, safe bulk ops, DRF permissions | Django or DRF work |
| [fastapi-engineering](plugins/backend/skills/fastapi-engineering/SKILL.md) | Sync vs async endpoints, dependencies, leak-proof response models, Pydantic v1/v2, lifespan | FastAPI or Starlette work |
| [api-design](plugins/backend/skills/api-design/SKILL.md) | Status semantics, stable error model, idempotency keys, pagination, compatible evolution | Adding or changing an API contract |
| [database-design](plugins/backend/skills/database-design/SKILL.md) | Ownership, keys, database-enforced invariants, history snapshots, query-derived indexes | New or changed tables, columns, indexes |
| [database-migrations](plugins/backend/skills/database-migrations/SKILL.md) | Expand-migrate-contract, non-blocking DDL, resumable backfills, rehearsal | Any schema or data migration |
| [mysql-engineering](plugins/backend/skills/mysql-engineering/SKILL.md) | EXPLAIN-verified indexes, isolation and locking, deadlock retries, lost updates, Aurora lag | MySQL/Aurora queries and concurrency |
| [redis-engineering](plugins/backend/skills/redis-engineering/SKILL.md) | TTL'd cache-aside, post-commit invalidation, stampede protection, token-checked locks | Caches, rate limits, locks in Redis |
| [distributed-systems](plugins/backend/skills/distributed-systems/SKILL.md) | Timeouts, bounded retries, unknown outcomes, outbox not dual writes, sagas, breakers | Calling or coordinating with other services |
| [async-messaging](plugins/backend/skills/async-messaging/SKILL.md) | SQS/SNS: FIFO vs standard, envelopes, idempotent consumers, visibility timeouts, DLQs | Publishing or consuming messages |
| [performance-engineering](plugins/backend/skills/performance-engineering/SKILL.md) | Percentile targets, profiling to the real bottleneck, same-conditions before/after | Something is slow, or an NFR is at risk |

### fintech-engineering

Scoped to credit scoring, eligibility and risk decisioning. Payments, ledgers and lending lifecycles are in an [extension catalog](plugins/fintech/README.md#extension-catalog-not-implemented), deliberately not built.

| Skill | What it does | Use when |
|---|---|---|
| [financial-data-integrity](plugins/fintech/skills/financial-data-integrity/SKILL.md) | Invariant catalog, immutable history, duplicate and lost-update prevention, reconciliation, migration evidence | Code that reads and updates financial records |
| [money-and-decimal-arithmetic](plugins/fintech/skills/money-and-decimal-arithmetic/SKILL.md) | Decimal from strings, explicit policy rounding, total-preserving allocation, string serialization | Computing, storing or serializing money and ratios |
| [credit-scoring-and-eligibility](plugins/fintech/skills/credit-scoring-and-eligibility/SKILL.md) | One policy source, versioned deterministic decisions, decision records, fallbacks, golden and parity tests | Scoring, eligibility, limits, decision services |
| [risk-decision-engineering](plugins/fintech/skills/risk-decision-engineering/SKILL.md) | Decision tables, precedence, missing values, gap/overlap validation, traced evaluation | Rule engines and policy configuration |
| [financial-authorization](plugins/fintech/skills/financial-authorization/SKILL.md) | Least privilege, maker-checker, amount-based authority, scoped service credentials | Back-office, overrides, limit or policy changes |
| [financial-auditability](plugins/fintech/skills/financial-auditability/SKILL.md) | Append-only audit records written atomically, separate from logs, reconstructable | Decisions, overrides, privileged access |
| [financial-system-reliability](plugins/fintech/skills/financial-system-reliability/SKILL.md) | Fail-closed choices, single effects, replay, decision-distribution canaries | Critical decision services, jobs, deployments |

### application-security

| Skill | What it does | Use when |
|---|---|---|
| [backend-security](plugins/security/skills/backend-security/SKILL.md) | Object-level authorization, mass assignment, injection, SSRF, webhook verification, secrets, abuse controls, each with an attack test | Endpoints, integrations, callbacks, auth |

### technical-writing

`blog-interviewer` → `blog-architect` → *(draft)* → `blog-visual-storyteller` → `blog-editor`

| Skill | What it does | Use when |
|---|---|---|
| [blog-interviewer](plugins/writing/skills/blog-interviewer/SKILL.md) | One-question-at-a-time interview to find the story and its evidence | Starting an engineering article |
| [blog-architect](plugins/writing/skills/blog-architect/SKILL.md) | Thesis, narrative structure, approved outline | After the interview |
| [blog-visual-storyteller](plugins/writing/skills/blog-visual-storyteller/SKILL.md) | SVG diagrams and memes embedded with `ImageCaption` | Illustrating an outline or draft |
| [blog-editor](plugins/writing/skills/blog-editor/SKILL.md) | Editorial, technical and publication review | Polishing a draft |

---

## Agent personas

| Agent | Plugin | Role | Authority |
|---|---|---|---|
| [engineering-orchestrator](plugins/engineering/agents/engineering-orchestrator.md) | spec-driven-engineering | Sequences stages and gates, assigns roles, keeps STATUS current | State documents only |
| [product-requirements-analyst](plugins/engineering/agents/product-requirements-analyst.md) | spec-driven-engineering | Discovery interviews, PRD analysis, decomposition, draft specs | Requirement documents only |
| [solution-architect](plugins/engineering/agents/solution-architect.md) | spec-driven-engineering | Designs, failure scenarios, observability plan, ADRs | Design documents only |
| [qa-engineer](plugins/engineering/agents/qa-engineer.md) | spec-driven-engineering | Independent verification against acceptance criteria | Read-only, runs tests |
| [code-reviewer](plugins/engineering/agents/code-reviewer.md) | spec-driven-engineering | Spec conformance and standards review | Read-only |
| [backend-engineer](plugins/backend/agents/backend-engineer.md) | python-backend | Implements approved tasks test-first, instrumented | Code within task scope |
| [database-engineer](plugins/backend/agents/database-engineer.md) | python-backend | Schema, migrations, backfills, query tuning | Migrations on local or test databases only |
| [observability-engineer](plugins/observability/agents/observability-engineer.md) | observability | Instrumentation, correlation and sensitive-logging review | Read-only |
| [security-auditor](plugins/security/agents/security-auditor.md) | application-security | Exploit-focused security audit | Read-only |
| [fintech-domain-reviewer](plugins/fintech/agents/fintech-domain-reviewer.md) | fintech-engineering | Decision logic vs approved credit and risk policy | Read-only |
| [financial-invariant-reviewer](plugins/fintech/agents/financial-invariant-reviewer.md) | fintech-engineering | Arithmetic, duplicates, concurrency, history, audit atomicity | Read-only |

Implementers never approve their own work. Read-only means `Write`/`Edit` are disallowed; `Bash` is kept for `git diff` and tests, so read-only through Bash is a rule of the role, backed by the guardrail hooks.

---

## Guardrail hooks

Deterministic checks only; judgment stays with skills and reviewers. **Deny** for high-confidence cases, **ask** for sensitive-but-legitimate operations, **feedback** for heuristics. Reasons never echo secret values. Full table and configuration: [engineering-guardrails README](plugins/guardrails/README.md).

| Group | Hooks |
|---|---|
| Secrets and files | `protect-sensitive-files`, `detect-secret-exposure`, `detect-hardcoded-credentials` |
| Destructive operations | `block-destructive-commands` (parsed commands, not substrings: force-push, `rm -rf` outside the project, DB drops, `terraform destroy`; asks before push, `reset --hard`, rebase) |
| Observability | `detect-sensitive-logging`, `validate-log-schema`, `check-observability-context` |
| Fintech and data | `protect-financial-core`, `protect-production-config`, `protect-database-migrations`, `financial-test-gate`, `migration-safety-check`, `sensitive-operation-audit` |
| Quality loop | `format-after-edit`, `lint-after-edit`, `typecheck-after-edit`, `verify-before-stop` (opt-in: `run_project_commands`) |
| Session | `session-context-init` (Software Factory state at session start and after compaction) |

Per-project configuration in `.claude/guardrails.json`:

```json
{
  "financial_core": ["src/eligibility/**", "src/credit/**"],
  "production_config": ["config/settings/production.py"],
  "logging": {"event_name_pattern": "^[a-z][a-z0-9_]*$"},
  "commands": {"lint": {"run": "ruff check {files}", "files": ["**/*.py"]}, "verify": "make test"}
}
```

Project `commands` come from the repository, so they run only after you enable the plugin option `run_project_commands` (`claude plugin configure engineering-guardrails@melvin-skills`).

---

## Evals

Native `claude plugin eval` suites per plugin: observability (the 12 required scenarios plus false-positive and must-not-trigger cases), product discovery, PRD analysis, fintech, and security. Each case pairs an `llm` rubric with concrete PASS/FAIL conditions, a `tool_used` grader that the expected skill fired, and, for sensitive data, a free `regex` grader that fails if the reply echoes the sentinel value.

```bash
claude plugin eval plugins/observability --case missing-error-context --runs 1 --ablation none
```

Model-graded runs cost usage: run the cases you touched, and read traces (`--keep-temp`) before changing a skill. Hooks and scripts use unit tests instead.

---

## How skills work

```
┌──────────────────────────────────────────────────────┐
│  SKILL.md                                            │
│  ┌─ Frontmatter ──────────────────────────────────┐  │
│  │ name: kebab-case (= directory)                 │  │
│  │ description: What it does. Use when ...       │  │
│  └────────────────────────────────────────────────┘  │
│  Overview             → problem it solves            │
│  When to use          → triggers, and when not       │
│  Inputs and context   → what to detect first         │
│  Process              → steps, decision criteria, ⏸  │
│  Output               → exact deliverable            │
│  Verification         → evidence, actually run       │
│  Escalation           → when a human decides         │
│  Rationalizations / Red flags                        │
└──────────────────────────────────────────────────────┘
references/  loaded on demand    scripts/  deterministic helpers
```

Design choices:

- **Inspect before prescribing.** Versions, conventions and existing abstractions are detected first; modern features are never assumed in a legacy project.
- **Evidence over assertion.** Verification means commands that were run, with their output; unknowns are labeled.
- **Humans decide.** Business rules, thresholds, fallbacks, destructive operations and releases are approval gates, never inferred.
- **Composable and lean.** Skills hand off by name instead of duplicating content; descriptions stay short because they are always in context.

---

## Project structure

| Path | Purpose |
|---|---|
| `.claude-plugin/marketplace.json` | The marketplace: one entry per plugin |
| `plugins/<profile>/.claude-plugin/plugin.json` | Plugin manifest: name, version, dependencies, `userConfig` |
| `plugins/<profile>/skills/`, `agents/`, `evals/` | Skills, agents and eval suites (default directories only) |
| `plugins/guardrails/` | `hooks.json`, hook scripts by event, shared `lib/`, `tests/` |
| `plugins/engineering/skills/factory-init/assets/factory/` | The Software Factory bundle: core standards, workflows, templates |
| `scripts/validate.py` | Validates marketplace, skills, agents, hooks, evals and links |
| `scripts/agent-skills`, `scripts/bootstrap.sh`, `scripts/profiles.json` | Install, update, doctor; new-machine setup; profiles |
| `docs/` | Architecture and conventions |

---

## Documentation

- [Architecture](docs/architecture.md): capability types, distribution model, workflows, state, evals, installation layers
- [Skill anatomy](docs/skill-anatomy.md), [agent anatomy](docs/agent-anatomy.md), [hook anatomy](docs/hook-anatomy.md): how each component is written
- [Adoption guide](docs/adoption-guide.md): profiles per project, project setup, daily use
- [Contribution guide](docs/contribution-guide.md): adding or changing components
- [Release strategy](docs/release-strategy.md): versions, updates, tags

---

## Checks

```bash
scripts/agent-skills validate                     # validator + hook tests + trace_check tests
claude plugin validate . && claude plugin validate plugins/<profile>
```

## Contributing

Components must be **specific** (actionable steps), **verifiable** (evidence-based exit criteria), **project-agnostic** (project facts live in the project), and **lean** (no duplicated content). Follow the [contribution guide](docs/contribution-guide.md): one meaningful module per commit, explicit staging, and a tree that validates at every commit.

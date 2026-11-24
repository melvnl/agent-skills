# melvin-skills

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/agent-skills-banner-dark.svg">
  <img src="docs/assets/agent-skills-banner-light.svg" alt="agent-skills: engineering skills, agents and guardrails for Claude Code" width="100%">
</picture>

**Engineering workflows, reviewer agents and guardrail hooks for Claude Code, packaged as plugins.**

- **Skills** say *how* to do a task, such as analyzing a PRD or breaking a spec into tasks.
- **Agents** say *who* does it and what they may touch, such as a read-only security reviewer.
- **Hooks** decide *what is allowed*: they block, ask or warn while Claude works.
- **Software Factory workflows** set *the order* of a change, with your approval at each gate.

Each project installs only the plugins it needs. Inspired by [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) and [mattpocock/skills](https://github.com/mattpocock/skills).

## What's inside

| | Count | Where |
|---|---|---|
| Plugins | 5 | `plugins/<profile>/` |
| Skills | 13 | `plugins/<profile>/skills/` |
| Specialist agents | 11 | `plugins/<profile>/agents/` |
| Guardrail hooks | 18 (113 unit tests) | `plugins/guardrails/` |
| Software Factory workflows | 11 (+ fintech overlay) | `plugins/engineering/skills/factory-init/assets/factory/workflows/` |
| Eval cases | 13 | `plugins/<profile>/evals/` |

## Quick start

```bash
git clone https://github.com/melvnl/agent-skills ~/dev/agent-skills
cd ~/dev/agent-skills
scripts/agent-skills install    # default profiles: core + guardrails, for every project
scripts/agent-skills doctor     # check the setup
```

On a new machine, `scripts/bootstrap.sh` does the clone, install and doctor in one step.

Then, optionally:

- **Add profiles to one project:** `~/dev/agent-skills/scripts/agent-skills install --profile backend --profile reviewers --scope project` (writes that project's `.claude/settings.json`).
- **Adopt the Software Factory in a repo:** run `/factory-init` inside it. After that, ask in plain language and `factory-router` picks the workflow.
- **Let guardrails format, lint, type-check and test as Claude works:** `claude plugin configure engineering-guardrails@melvin-skills` and turn on `run_project_commands`. The formatter and linter are auto-detected from your project (ruff, biome, prettier, eslint, gofmt); type checks and tests need `commands` in `.claude/guardrails.json`.

To update a local checkout, `git pull` and start a new session (or run `/reload-plugins`). Manual install and versioned updates: [release strategy](docs/release-strategy.md).

## Profiles

| Profile | Plugin | What you get | Installed by default |
|---|---|---|---|
| `core` | [spec-driven-engineering](plugins/engineering/README.md) | 9 skills and 5 agents: Software Factory, product discovery, PRD analysis, specs, planning, implementation loop | yes |
| `guardrails` | [engineering-guardrails](plugins/guardrails/README.md) | 18 hooks, active in every session | yes |
| `backend` | [backend-engineering](plugins/backend/README.md) | 2 implementer agents: backend and database engineer (pulls in `core`) | no |
| `reviewers` | [reviewers](plugins/reviewers/README.md) | 4 read-only reviewer agents: observability, security, fintech policy, financial invariants | no |
| `writing` | [technical-writing](plugins/writing/README.md) | 4 skills for writing engineering blog posts | no |

`all` installs every plugin. Typical choices: a backend service adds `backend` and `reviewers`; a blog repo only needs `writing`.

## Guardrails: what runs when

All 18 hooks are in `engineering-guardrails`. They check facts a pattern can decide (a path, a parsed command, a known secret format) and leave judgment to skills and reviewers. Messages never repeat a secret value.

| When | Hooks | What they can do |
|---|---|---|
| Session starts (also on resume, `/clear`, compaction) | 1 | Add context to the session |
| Before a tool runs | 7 | **Block** the call, or **ask you** first |
| After a tool runs | 9 | **Report** a problem back so Claude fixes it |
| Claude finishes its reply | 1 | Keep Claude working until checks pass |
| Session ends | 0 | |

**Session start (1)**

| Hook | Does |
|---|---|
| `session-context-init` | Adds the code clarity rule in every repo, and lists which formatter and linter will run. In Software Factory repos, also adds the session protocol, task status and git state. |

**Before a tool runs (7)**

| Hook | Does |
|---|---|
| `protect-sensitive-files` | Blocks reading or writing `.env` files, keys and credential files. |
| `block-destructive-commands` | Blocks force-push, `rm -rf` outside the project, database drops, `terraform destroy`. Asks before push, `reset --hard`, rebase, amend. |
| `detect-secret-exposure` | Blocks writes and commands that contain a known secret format. |
| `protect-financial-core` | Asks before editing paths you list as `financial_core`. |
| `protect-production-config` | Asks before editing production settings, deploy, Kubernetes, Helm or Terraform files. |
| `protect-database-migrations` | Asks before editing a migration that is already committed. |
| `financial-test-gate` | Blocks a commit that changes `financial_core` code without changing a test. |

**After a tool runs (9)**

| Hook | Does |
|---|---|
| `detect-hardcoded-credentials` | Reports credential variables set to string literals. |
| `detect-sensitive-logging` | Reports log calls that include sensitive fields, headers or whole requests. |
| `validate-log-schema` | Reports log event names that don't match your pattern (only if you set one). |
| `check-observability-context` | Reports SQS/SNS calls that drop tracing context. |
| `migration-safety-check` | Reports migration steps that drop data or lock tables. |
| `sensitive-operation-audit` | Quietly records sensitive actions, with secrets removed, to an audit log. |
| `format-after-edit` | Runs your formatter on the edited file: configured, or auto-detected. Opt-in. |
| `lint-after-edit` | Runs your linter on the edited file: configured, or auto-detected. Opt-in. |
| `typecheck-after-edit` | Runs your type checker on the edited file. Opt-in. |

**Claude finishes its reply (1)**

| Hook | Does |
|---|---|
| `verify-before-stop` | Runs your verify command when files changed, and keeps Claude working once if it fails. Opt-in. |

"Opt-in" hooks run project tools, so they stay off until you enable `run_project_commands`. The formatter and linter are found automatically when the project configures and installs one (for example `[tool.ruff]` plus `.venv/bin/ruff`). When a check can't run, for an unknown file type or a missing tool, you and Claude are told once per session, and the session start lists what will run. Commands, paths and turned-off hooks go in `.claude/guardrails.json`:

```json
{
  "financial_core": ["src/eligibility/**", "src/credit/**"],
  "commands": {"lint": "ruff check {files}", "verify": "make test"},
  "disabled": ["code-clarity"]
}
```

All options: [engineering-guardrails README](plugins/guardrails/README.md).

## How a change moves through the Software Factory

For a prd-driven feature:

1. `factory-router` recognizes "implement this PRD" and starts `prd-to-implementation`.
2. `prd-analysis` lists contradictions, ambiguities and missing requirements. **You resolve them.**
3. `specification-decomposition` and `acceptance-criteria-engineering` write specs with stable ids. **You approve them.**
4. `solution-architect` writes the design, including failure cases and logging.
5. `planning-and-task-breakdown` orders the tasks; `backend-engineer` implements each one test-first with `loop-engineering`.
6. `qa-engineer` verifies and the reviewers review. The implementer never approves its own work.
7. **You approve the release.**

Progress lives in the project (`tasks/status.md`, specs, task files), so any session can pick up where the last one stopped.

| Workflow | Use when |
|---|---|
| `new-feature` | Adding or extending a capability |
| `fintech-feature` (overlay) | The change affects credit, eligibility, risk, limits or money |
| `prd-to-implementation` | Building from a large requirements document |
| `bug-fix` | Behavior differs from the spec |
| `production-incident` | Production is broken, degraded or leaking data |
| `database-migration` | Schema changes and backfills |
| `refactoring` | Better internals, same behavior |
| `code-review` | Any change |
| `security-review` | Endpoints, integrations, auth, secrets |
| `observability-review` | Backend changes |
| `resume-work`, `new-project` | Continuing work; starting a project |

## Skills

**spec-driven-engineering**

| Skill | Use when |
|---|---|
| [factory-init](plugins/engineering/skills/factory-init/SKILL.md) | Setting up or checking the Software Factory in a repo (`/factory-init [--verify]`) |
| [factory-router](plugins/engineering/skills/factory-router/SKILL.md) | Any development request in a factory repo |
| [product-discovery](plugins/engineering/skills/product-discovery/SKILL.md) | You have an idea but no PRD |
| [prd-analysis](plugins/engineering/skills/prd-analysis/SKILL.md) | A PRD or requirements document arrives |
| [specification-decomposition](plugins/engineering/skills/specification-decomposition/SKILL.md) | Cutting analyzed requirements into buildable feature specs |
| [acceptance-criteria-engineering](plugins/engineering/skills/acceptance-criteria-engineering/SKILL.md) | Writing or reviewing what "done" means |
| [requirement-traceability](plugins/engineering/skills/requirement-traceability/SKILL.md) | Checking PRD → spec → task → code → test links before closing a feature |
| [planning-and-task-breakdown](plugins/engineering/skills/planning-and-task-breakdown/SKILL.md) | Turning an approved spec into ordered tasks |
| [loop-engineering](plugins/engineering/skills/loop-engineering/SKILL.md) | Implementing a task list, with stop conditions |

**technical-writing:** interview → outline → draft → visuals → edit

| Skill | Use when |
|---|---|
| [blog-interviewer](plugins/writing/skills/blog-interviewer/SKILL.md) | Starting an article: finding the story and its evidence |
| [blog-architect](plugins/writing/skills/blog-architect/SKILL.md) | Turning the interview into a thesis and outline |
| [blog-visual-storyteller](plugins/writing/skills/blog-visual-storyteller/SKILL.md) | Adding diagrams to an outline or draft |
| [blog-editor](plugins/writing/skills/blog-editor/SKILL.md) | Polishing a draft for publication |

## Agents

| Agent | Plugin | Role | May change |
|---|---|---|---|
| [engineering-orchestrator](plugins/engineering/agents/engineering-orchestrator.md) | spec-driven-engineering | Runs the stages and gates, keeps status current | Status documents |
| [product-requirements-analyst](plugins/engineering/agents/product-requirements-analyst.md) | spec-driven-engineering | Discovery, PRD analysis, draft specs | Requirement documents |
| [solution-architect](plugins/engineering/agents/solution-architect.md) | spec-driven-engineering | Designs and ADRs | Design documents |
| [qa-engineer](plugins/engineering/agents/qa-engineer.md) | spec-driven-engineering | Verifies against acceptance criteria | Nothing (runs tests) |
| [code-reviewer](plugins/engineering/agents/code-reviewer.md) | spec-driven-engineering | Reviews against spec and standards | Nothing |
| [backend-engineer](plugins/backend/agents/backend-engineer.md) | backend-engineering | Implements approved tasks test-first | Code in the task's scope |
| [database-engineer](plugins/backend/agents/database-engineer.md) | backend-engineering | Schema, migrations, backfills, queries | Local or test databases |
| [observability-engineer](plugins/reviewers/agents/observability-engineer.md) | reviewers | Reviews logging, tracing and sensitive data in logs | Nothing |
| [security-auditor](plugins/reviewers/agents/security-auditor.md) | reviewers | Security review with exploit scenarios | Nothing |
| [fintech-domain-reviewer](plugins/reviewers/agents/fintech-domain-reviewer.md) | reviewers | Checks decision logic against the approved credit policy | Nothing |
| [financial-invariant-reviewer](plugins/reviewers/agents/financial-invariant-reviewer.md) | reviewers | Checks money arithmetic, duplicates, concurrency, audit records | Nothing |

## Evals

A skill or rule stays only if it beats plain Claude in a with-and-without eval; knowledge-only skills were removed for that reason. Suites cover product discovery, PRD analysis and the code clarity rule.

```bash
claude plugin eval plugins/engineering --case missing-nfrs --runs 1 --ablation none
```

Evals cost usage, so run the cases you changed. Hooks and scripts are covered by unit tests instead.

## Working on this repo

```bash
scripts/agent-skills validate                                   # validator, hook tests, trace_check tests
claude plugin validate . && claude plugin validate plugins/<profile>
```

| Path | Holds |
|---|---|
| `.claude-plugin/marketplace.json` | One entry per plugin |
| `plugins/<profile>/` | A plugin: manifest, `skills/`, `agents/`, `evals/` |
| `plugins/guardrails/` | `hooks.json`, hook scripts by event, shared `lib/`, `tests/` |
| `plugins/engineering/skills/factory-init/assets/factory/` | The Software Factory: standards, workflows, templates |
| `scripts/` | `agent-skills` (install, update, doctor, validate), `bootstrap.sh`, `validate.py`, `profiles.json` |

Docs: [architecture](docs/architecture.md), [skill](docs/skill-anatomy.md), [agent](docs/agent-anatomy.md) and [hook](docs/hook-anatomy.md) anatomy, [adoption guide](docs/adoption-guide.md), [contribution guide](docs/contribution-guide.md), [release strategy](docs/release-strategy.md).

Contributions follow the [contribution guide](docs/contribution-guide.md): one meaningful change per commit, explicit staging, and every commit passes validation.

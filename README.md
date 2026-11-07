# melvin-skills

A portable, version-controlled set of Claude Code capabilities, split into installable profiles: engineering skills, specialist agents, deterministic guardrail hooks, and the spec-driven **Software Factory**.

Inspired by [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (lifecycle-ordered, process-heavy skills) and [mattpocock/skills](https://github.com/mattpocock/skills) (small, composable skills).

## Plugins (profiles)

The repository is a Claude Code **marketplace**. Each directory under `plugins/` is one self-contained plugin; install only the profiles a project needs.

| Plugin | Contents |
|---|---|
| [melvin-engineering](plugins/engineering/README.md) | Software Factory, spec-driven planning and execution |
| [melvin-backend](plugins/backend/README.md) | Python, Django, FastAPI, APIs, databases, MySQL, Redis, messaging, performance |
| [melvin-observability](plugins/observability/README.md) | Structured logging, correlation, PII-safe logging, observability review |
| [melvin-writing](plugins/writing/README.md) | Engineering blog pipeline |

### melvin-engineering

- **[factory-init](plugins/engineering/skills/factory-init/SKILL.md)**: Installs the `.factory/` spec-driven software factory into a repo, populates project docs from evidence, and verifies it.
- **[factory-router](plugins/engineering/skills/factory-router/SKILL.md)**: Classifies and sizes every request in a factory repo and routes it to the right workflow and approval gates.
- **[prd-analysis](plugins/engineering/skills/prd-analysis/SKILL.md)**: Analyzes a large or AI-generated PRD: requirements with source refs, contradictions, ambiguities, duplicates, missing NFRs.
- **[specification-decomposition](plugins/engineering/skills/specification-decomposition/SKILL.md)**: Turns analyzed requirements into stable ids, domain groups, a feature catalog, and atomic feature specs with traceability.
- **[acceptance-criteria-engineering](plugins/engineering/skills/acceptance-criteria-engineering/SKILL.md)**: Writes and reviews atomic, testable Given/When/Then criteria covering boundaries, permissions, state, failures, idempotency, time, money, observability and audit.
- **[requirement-traceability](plugins/engineering/skills/requirement-traceability/SKILL.md)**: Keeps the requirement → feature → AC → task → code → test chain intact, with a deterministic checker for untraced or dangling ids.
- **[planning-and-task-breakdown](plugins/engineering/skills/planning-and-task-breakdown/SKILL.md)**: Breaks an approved spec into small, ordered, verifiable tasks with AC coverage, test and instrumentation requirements, and done-when conditions.
- **[loop-engineering](plugins/engineering/skills/loop-engineering/SKILL.md)**: Runs each task as a closed loop (implement, instrument, test, diagnose, fix, verify, checkpoint) with explicit stop conditions and persisted state.
- **[context-engineering](plugins/engineering/skills/context-engineering/SKILL.md)**: Keeps the context window focused: targeted reading, bounded output, state in files, chunked large documents, subagent exploration, compaction-proof handoffs.
- **[test-driven-development](plugins/engineering/skills/test-driven-development/SKILL.md)**: Red-green-refactor from the acceptance criteria: each test observed failing for the right reason, minimal change, refactor under green. Python/pytest aware.
- **[debugging-and-error-recovery](plugins/engineering/skills/debugging-and-error-recovery/SKILL.md)**: Diagnoses from evidence: reproduce, minimize, one hypothesis at a time, bisect, root cause, same pattern elsewhere, and safe recovery to green.
- **[git-workflow](plugins/engineering/skills/git-workflow/SKILL.md)**: Small Conventional Commits with explicit staging and reviewed diffs; no unrelated changes, secrets, history rewrites or pushes without approval.

### melvin-backend

- **[python-backend-engineering](plugins/backend/skills/python-backend-engineering/SKILL.md)**: Version-safe Python backend code: typed boundaries, explicit timeouts, aware datetimes, Decimal money, exception chaining, pure domain logic.
- **[django-engineering](plugins/backend/skills/django-engineering/SKILL.md)**: Version-correct Django/DRF: service-layer rules, constraints, efficient querysets, transactions with on_commit side effects, safe bulk ops, explicit permissions.
- **[fastapi-engineering](plugins/backend/skills/fastapi-engineering/SKILL.md)**: Version-correct FastAPI/Pydantic: sync vs async endpoints, auth and session dependencies, leak-proof response models, safe errors, lifespan, durable work on queues.
- **[api-design](plugins/backend/skills/api-design/SKILL.md)**: HTTP contracts: status semantics, a stable error model, idempotency keys, pagination, money and time formats, compatible evolution, contract tests.

### melvin-observability

- **[structured-logging-and-instrumentation](plugins/observability/skills/structured-logging-and-instrumentation/SKILL.md)**: Decides what deserves a log entry and adds structured, correlated, PII-safe logs using the project's existing logger.
- **[distributed-tracing-and-correlation](plugins/observability/skills/distributed-tracing-and-correlation/SKILL.md)**: Preserves request, correlation and trace context across HTTP, SQS/SNS, workers and async code.
- **[logging-security-and-redaction](plugins/observability/skills/logging-security-and-redaction/SKILL.md)**: Keeps secrets, PII and customer financial data out of logs through allowlisted fields, masking or keyed pseudonyms.
- **[observability-engineering](plugins/observability/skills/observability-engineering/SKILL.md)**: Designs logs, metrics and traces for a feature: health and dependency signals, cardinality, SLO-based alerting, the observability plan.
- **[observability-code-review](plugins/observability/skills/observability-code-review/SKILL.md)**: Reviews a backend diff for observability gaps and over-instrumentation, correlation loss, wrong severity, sensitive data, unbounded labels.

### melvin-writing

`blog-interviewer` → `blog-architect` → *(draft)* → `blog-visual-storyteller` → `blog-editor`

- **[blog-interviewer](plugins/writing/skills/blog-interviewer/SKILL.md)**: Interviews you, one question at a time, to find the story worth publishing and the evidence behind it.
- **[blog-architect](plugins/writing/skills/blog-architect/SKILL.md)**: Turns an interview summary into a thesis, narrative structure, and approved outline.
- **[blog-visual-storyteller](plugins/writing/skills/blog-visual-storyteller/SKILL.md)**: Designs SVG diagrams and memes for the article and embeds them with `ImageCaption`.
- **[blog-editor](plugins/writing/skills/blog-editor/SKILL.md)**: Reviews a draft for technical accuracy, narrative, style, and publication readiness.

## Install

```bash
claude plugin marketplace add /path/to/agent-skills     # or the GitHub repo once pushed
claude plugin install melvin-engineering@melvin-skills
claude plugin install melvin-writing@melvin-skills
```

To pick up changes: bump `version` in the plugin's `.claude-plugin/plugin.json`, then run `claude plugin marketplace update melvin-skills` and `claude plugin update <plugin>@melvin-skills`.

## Layout

```
.claude-plugin/marketplace.json   the marketplace: one entry per plugin
plugins/<profile>/
  .claude-plugin/plugin.json      plugin manifest (name, version, dependencies)
  README.md                       what the plugin contains
  skills/<skill>/SKILL.md         skills (+ references/, scripts/, assets/ as needed)
scripts/validate.py               lint marketplace, plugins, skills, links
docs/skill-anatomy.md             how a skill is written here
```

## Contributing

1. Read [docs/skill-anatomy.md](docs/skill-anatomy.md).
2. Add the skill under `plugins/<profile>/skills/`, then link it from this README and the plugin's README.
3. Run `python3 scripts/validate.py` until it reports `0 FAIL`, and `claude plugin validate plugins/<profile>`.

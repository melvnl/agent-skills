# Software Factory

A reusable, **project-agnostic**, spec-driven engineering process for humans and AI coding agents. Copy this directory into any repository (web, mobile, backend, API, SaaS, internal tool, AI application) and supply project context outside it.

| Directory | Contents | Use |
|---|---|---|
| `core/` | `principles`, `engineering-standards`, `coding-standards`, `testing-standards`, `definition-of-done`, `agent-behavior` | Always-on rules |
| `workflows/` | `new-project`, `new-feature` (+ `fintech-feature` overlay), `prd-to-implementation`, `bug-fix`, `production-incident`, `database-migration`, `refactoring`, `code-review`, `security-review`, `observability-review`, `resume-work` | Step-by-step procedures with entry and exit conditions, gates, and approvals |
| `templates/` | `project-brief`, `PRD`, `feature-spec`, `technical-design`, `task-breakdown`, `architecture-decision-record`, `implementation-report` | Starting points for project documents |

## Adopting in a new project

1. Copy `.factory/` unchanged.
2. Follow `workflows/new-project.md` to create the project's `product/`, `engineering/`, `specs/`, `tasks/`, and agent entry point (`CLAUDE.md`).
3. Declare the concrete stack, commands, and conventions in project docs — not here.
4. Optional: copy the companion `factory-router` Claude Code skill (`.claude/skills/factory-router/`), which is also project-agnostic. It classifies plain-language requests and routes them to these workflows. The project's `CLAUDE.md` remains the entry point and supplies project paths.

Shortcut: the `factory-init` Claude Code skill automates steps 1–4 for an existing or empty repository. It bundles this directory and `factory-router`, inspects the stack, populates project docs from evidence, creates or merges `CLAUDE.md`, never overwrites existing files without approval, and verifies files and cross-references with its `verify_factory.sh` script. When the skills come from an installed plugin, copying `factory-router` into the project is optional.

## Coverage gaps

Investigation, architecture questions, documentation changes, and general questions have no workflow file here. The `factory-router` skill defines minimal interim protocols for them. Promote them to `workflows/` if they need gates or templates.

## Rules for changing the factory

- Keep it project-agnostic: no product names, domain terms, schemas, or specific technology mandates.
- Changes should improve every project that uses it; project-specific exceptions belong in that project's docs.

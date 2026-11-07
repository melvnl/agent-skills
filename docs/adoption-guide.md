# Adoption guide

How to use these plugins on a machine and in real projects.

## 1. Set up a machine

```bash
git clone <repo-url> ~/dev/agent-skills          # or: scripts/bootstrap.sh --repo <repo-url> --profile core
~/dev/agent-skills/scripts/agent-skills install --profile core --profile guardrails
~/dev/agent-skills/scripts/agent-skills doctor
```

User-scope installs apply to every project. Requirements: Claude Code, `git`, `python3` 3.8+ (guardrail hooks).

## 2. Choose profiles per project

| Project type | Profiles | Scope |
|---|---|---|
| Engineering blog / writing | `writing` | project |
| Fintech backend (credit, eligibility, risk) | `fintech` (pulls backend, observability, security), `guardrails` | project |
| Other Python backends, e-commerce, automation | `backend` (pulls observability), `guardrails` | project |
| Small experiments | `core` | user |

`--scope project` writes the plugin enablement to the project's `.claude/settings.json`, which can be committed so collaborators get the same set. `--scope local` keeps it in `.claude/settings.local.json` (not committed).

```bash
cd ~/work/eligibility-service
~/dev/agent-skills/scripts/agent-skills install --profile fintech --profile guardrails --scope project
```

## 3. Set up a project

1. **Software Factory** (spec-driven projects): in the project, run `/factory-init`. It inspects the stack, installs `.factory/`, populates `product/`, `engineering/`, `tasks/STATUS.md` from evidence, and creates or merges `CLAUDE.md`, asking before touching anything that exists. When the engineering plugin is installed, the router copy in `.claude/skills/` is optional.
2. **Guardrails configuration** (optional): add `.claude/guardrails.json` declaring what only the project knows:

   ```json
   {
     "financial_core": ["src/eligibility/**", "src/credit/**"],
     "production_config": ["config/settings/production.py"],
     "migrations": ["**/migrations/*.py"],
     "logging": {"event_name_pattern": "^[a-z][a-z0-9_]*$"},
     "commands": {
       "format": "ruff format {files}",
       "lint": {"run": "ruff check {files}", "files": ["**/*.py"]},
       "typecheck": {"run": "mypy {files}", "files": ["src/**/*.py"], "timeout": 120},
       "verify": "make test"
     }
   }
   ```

   The `commands` run only after you enable the plugin option `run_project_commands` (`claude plugin configure melvin-guardrails@melvin-skills`), because they come from the repository.
3. **Logging conventions**: record the project's logger, standard fields, and correlation mechanism in `engineering/DEVELOPMENT_GUIDE.md` (the observability skills read them before writing log calls).
4. **Data classification**: record approved identifiers and sensitive fields in `engineering/SECURITY_AND_PRIVACY.md` (the redaction skill and reviewers use it).

## 4. Daily use

- Ask in plain language. In factory projects, `factory-router` classifies the request and picks the workflow (feature, PRD, bug, incident, migration, review, …) with its approval gates.
- Large PRDs: ask to analyze the document first; the PRD-to-implementation workflow stops for your decisions on contradictions and ambiguities.
- Reviews: ask for an observability, security, fintech-domain, or invariant review; the read-only reviewer agents report findings without editing.
- Resuming: say "continue"; state comes from `tasks/STATUS.md` and the task files, not from conversation memory.

## 5. Keep up to date

- Local checkout: `git pull` in the repo; changes apply at the next session start or `/reload-plugins`.
- GitHub-hosted marketplace: `scripts/agent-skills update`.

## 6. What lives where

| Layer | Location | In this repo? |
|---|---|---|
| Reusable capabilities | `plugins/` | yes |
| Personal Claude Code configuration | `~/.claude/` | no |
| Project configuration | `<project>/.claude/settings.json`, `.claude/guardrails.json` | no |
| Project engineering state | `.factory/`, `product/`, `engineering/`, `specs/`, `tasks/` | no |

Never commit credentials, production configuration, or employer-confidential information here.

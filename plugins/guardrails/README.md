# melvin-guardrails

Deterministic guardrail hooks for Claude Code. Each hook checks a fact a pattern can decide (a protected path, a parsed destructive command, a known secret format, a logger call containing an authorization header) and **denies**, **asks**, or **feeds a finding back**. Judgment calls such as "is this log useful?" stay with skills and reviewer agents.

Pattern matching is not proof: a clean result doesn't mean no secret, PII, or destructive effect exists.

## Requirements

- `python3` 3.8+ on `PATH` (standard library only).

## Configuration

Optional, per project: `<project>/.claude/guardrails.json`. Every key is optional; defaults apply when the file is absent.

```json
{
  "disabled": ["format-after-edit"],
  "protected_paths": ["config/secrets/**"],
  "financial_core": ["src/credit/**", "src/eligibility/**"],
  "production_config": ["config/settings/production.py", "deploy/prod/**"],
  "migrations": ["**/migrations/*.py", "db/migrations/*.sql"],
  "commands": {"format": "ruff format {files}", "lint": "ruff check {files}", "typecheck": "mypy {files}", "verify": "make test"},
  "logging": {"event_name_pattern": "^[a-z][a-z0-9_]*$"}
}
```

### Running project commands (opt-in)

`format-after-edit`, `lint-after-edit`, `typecheck-after-edit` and `verify-before-stop` run commands that come from the repository's `guardrails.json`. A cloned repository could put anything there, so these hooks do nothing until you enable the plugin option **`run_project_commands`** (`/config`, or the prompt shown when the plugin is enabled). Enable it only if you trust the repositories you open. The hooks never guess a tool: an unconfigured command is skipped.

## Hooks

| Hook | Event | Matcher | Behavior |
|---|---|---|---|
| `protect-sensitive-files` | PreToolUse | `Read\|Edit\|Write\|MultiEdit\|NotebookEdit\|Grep\|Bash` | Denies reading or writing `.env`, keys and credential files, including via parsed Bash commands; templates allowed. |
| `block-destructive-commands` | PreToolUse | `Bash` | Parses commands; denies catastrophic ones (force-push, `rm -rf` outside the project, DB drops, `terraform destroy`, S3 deletion); asks before push, `reset --hard`, `clean -f`, rebase, amend. |
| `detect-secret-exposure` | PreToolUse | `Write\|Edit\|MultiEdit\|Bash` | Denies new content or commands containing known secret formats (AWS, private keys, GitHub, Slack, Stripe, JWT, URL credentials); reports pattern and line, never the value. |
| `detect-hardcoded-credentials` | PostToolUse | `Write\|Edit\|MultiEdit` | Feeds back credential-named variables assigned string literals (`password = "..."`), with file:line; skips tests, examples and placeholders. |
| `format-after-edit` | PostToolUse | `Write\|Edit\|MultiEdit` | Opt-in: runs the project's `commands.format` on the edited file; asks Claude to re-read a reformatted file; feeds back formatter failures. |
| `lint-after-edit` | PostToolUse | `Write\|Edit\|MultiEdit` | Opt-in: runs the project's `commands.lint` on the edited file and feeds back reported problems. |
| `typecheck-after-edit` | PostToolUse | `Write\|Edit\|MultiEdit` | Opt-in: runs the project's `commands.typecheck` on the edited file and feeds back type errors. |
| `verify-before-stop` | Stop | `*` | Opt-in: when the working tree changed, runs the project's `commands.verify` before Claude finishes and blocks the stop once on failure; `stop_hook_active` prevents loops. |
| `session-context-init` | SessionStart | `startup\|resume\|clear\|compact` | In Software Factory repos, adds the session protocol reminder, a bounded STATUS snapshot, git state and configured protections; after compaction, a re-verify reminder. |
| `detect-sensitive-logging` | PostToolUse | `Write\|Edit\|MultiEdit` | Feeds back Python log calls whose fields, keys or f-string expressions name sensitive data, or that log whole requests, headers or objects; message words are not flagged. |
| `validate-log-schema` | PostToolUse | `Write\|Edit\|MultiEdit` | When `logging.event_name_pattern` is configured: new Python log calls must use a constant event name matching it, not f-strings, formatting or concatenation. |
| `check-observability-context` | PostToolUse | `Write\|Edit\|MultiEdit` | Feeds back SQS/SNS publishes without `MessageAttributes` and SQS receives without `MessageAttributeNames` (lost correlation context). |
| `protect-financial-core` | PreToolUse | `Edit\|Write\|MultiEdit` | Asks before editing paths the project lists as `financial_core` (no defaults), pointing to the fintech overlay gates. |
| `protect-production-config` | PreToolUse | `Edit\|Write\|MultiEdit` | Asks before editing production settings, prod deploy, Kubernetes, Helm and Terraform paths (defaults plus `production_config`). |
| `protect-database-migrations` | PreToolUse | `Edit\|Write\|MultiEdit` | Asks before editing a migration file that is already committed (it may have run); new migrations and `__init__.py` pass. |

## Development

```bash
python3 -m unittest discover -s plugins/guardrails/tests
```

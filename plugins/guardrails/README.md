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

## Development

```bash
python3 -m unittest discover -s plugins/guardrails/tests
```

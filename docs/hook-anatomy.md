# Hook anatomy

How a guardrail hook in this repo is written. Contract: Claude Code hooks (https://code.claude.com/docs/en/hooks).

A hook decides **which operations are allowed, blocked, or flagged, and when**, deterministically. Hooks never make judgment calls such as "is this log useful?". That belongs to skills (`structured-logging-and-instrumentation`) and reviewer agents (`observability-engineer`). A hook checks facts that a pattern can decide: a path matches a protected glob, a command parses to `git push --force`, a logger call contains `authorization`.

## Location

```
plugins/guardrails/
  .claude-plugin/plugin.json      "hooks": "./hooks.json"
  hooks.json                      registrations (event, matcher, command)
  lib/                            shared stdlib-only helpers: I/O contract, config, patterns
  pre-tool-use/<hook>.py
  post-tool-use/<hook>.py
  stop/<hook>.py
  session/<hook>.py
  tests/test_<hook>.py            unittest; run: python3 -m unittest discover -s plugins/guardrails/tests
```

Python 3.8+ standard library only. No third-party imports, no network access.

## Registration

Exec form, so paths with spaces stay one argument and no shell re-parses input:

```json
{ "type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/pre-tool-use/block-destructive-commands.py"], "timeout": 10 }
```

Use the narrowest `matcher` (`Bash`, `Edit|Write`). Matching hooks run **in parallel**, including user-level hooks such as RTK's Bash rewriter. A hook sees the command as Claude sent it, not as another hook rewrote it.

## I/O contract

Input is one JSON object on stdin: common fields `session_id`, `cwd`, `hook_event_name`, `permission_mode`; tool events add `tool_name`, `tool_input` (`command` for Bash; `file_path`, `content`, `old_string`, `new_string` for Write/Edit); PostToolUse adds `tool_response`; Stop adds `stop_hook_active`; SessionStart adds `source`.

| Outcome | How |
|---|---|
| Allow silently | exit 0, no output |
| **Deny** a tool call (PreToolUse) | exit 0 + `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}` |
| **Ask** the human (PreToolUse) | same, with `"permissionDecision": "ask"` |
| Feed a finding back after a tool ran (PostToolUse) | exit 0 + `{"decision": "block", "reason": "..."}`. The edit stays; Claude must address the reason |
| Keep Claude working (Stop) | exit 0 + `{"decision": "block", "reason": "..."}`, **only** when `stop_hook_active` is false |
| Add session context (SessionStart) | exit 0 + `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}` |
| Internal error (bad input, bug) | exit 1 with a one-line stderr message. Claude Code shows a non-blocking hook error notice; the action proceeds |

**Severity policy.** `deny` is reserved for high-confidence matches (known secret formats, destructive commands, protected files). `ask` is for legitimate-but-sensitive operations (editing financial core, production config, committed migrations). Heuristic findings (possible PII in a log call) use PostToolUse feedback, never `deny`, because false positives must not block work.

**Fail-open rationale.** A crashing guardrail must not lock the session, so internal errors exit 1 (visible, non-blocking). Every hook is unit-tested so this path stays rare.

## Reasons are actionable and secret-free

- Say what matched, where (`file:line`), why it matters, and the safe alternative.
- **Never echo a matched secret or PII value.** Report the pattern name and location only.
- Keep reasons under ~600 characters.

## Project configuration

Hooks read optional `<project>/.claude/guardrails.json` (via `$CLAUDE_PROJECT_DIR`, falling back to the input `cwd`). Every key is optional, and absent config means safe built-in defaults:

```json
{
  "disabled": ["format-after-edit"],
  "protected_paths": ["config/secrets/**"],
  "financial_core": ["src/credit/**", "src/eligibility/**"],
  "production_config": ["config/settings/production.py", "deploy/prod/**"],
  "migrations": ["**/migrations/*.py", "db/migrations/*.sql"],
  "commands": {
    "format": "ruff format {files}",
    "lint": "ruff check {files}",
    "typecheck": "mypy {files}",
    "verify": "make test"
  },
  "logging": { "event_name_pattern": "^[a-z][a-z0-9_]*$" }
}
```

`{files}` expands to the edited file paths, shell-quoted. Command hooks run only what the project configures and never guess a tool.

## Performance

- Target < 100 ms per invocation for pattern hooks. External commands (format, lint, typecheck, verify) honor a timeout and report a timeout as a finding, not a pass.
- Read only what the decision needs: the tool input, or the edited file for PostToolUse checks.

## Tests

Each hook has `tests/test_<hook>.py` covering: a **true positive** (blocked or flagged), a **true negative** (allowed), at least one **known false-positive trap** that must pass (e.g. `.env.example`, `rm -rf ./build`, `user_id` in a log), and malformed input (exit 1, no traceback on stdout).

## Limitations (stated, not hidden)

Pattern matching is not proof. A clean hook result does not mean no secret, PII, or destructive effect exists. Hooks are the deterministic first line; skills, reviewer agents, and humans remain responsible for judgment.

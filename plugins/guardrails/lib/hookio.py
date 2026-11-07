"""Claude Code hook I/O contract helpers. Stdlib only; Python 3.8+.

Every hook script calls `run(main)`. `main(data)` receives the parsed stdin JSON and returns nothing
(allow silently) or calls one of the emit helpers, which print the documented JSON and exit 0.
Internal errors exit 1 with a one-line stderr message: Claude Code shows a non-blocking notice and the
action proceeds (fail-open by design; see docs/hook-anatomy.md).
"""
import json
import os
import sys

MAX_REASON = 600


class HookError(Exception):
    """A problem with the hook's input or environment (reported, never blocking)."""


def read_input(stream=None):
    raw = (stream or sys.stdin).read()
    try:
        data = json.loads(raw) if raw.strip() else None
    except ValueError as exc:
        raise HookError("hook input is not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise HookError("hook input must be a JSON object")
    return data


def _clip(text):
    text = " ".join(str(text).split()) if "\n" not in str(text) else str(text).strip()
    return text if len(text) <= MAX_REASON else text[: MAX_REASON - 3] + "..."


def _emit(payload):
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write("\n")
    sys.stdout.flush()
    sys.exit(0)


def deny(reason):
    """PreToolUse: block the tool call; the reason is shown to Claude."""
    _emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                  "permissionDecisionReason": _clip(reason)}})


def ask(reason):
    """PreToolUse: ask the human to confirm the tool call."""
    _emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                  "permissionDecisionReason": _clip(reason)}})


def feedback(reason):
    """PostToolUse / Stop: `decision: block` with a reason Claude must address."""
    _emit({"decision": "block", "reason": _clip(reason)})


def add_context(event, text):
    """SessionStart (and other events supporting it): add context for Claude."""
    _emit({"hookSpecificOutput": {"hookEventName": event, "additionalContext": str(text)[:9000]}})


def project_dir(data):
    return os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()


def tool_input(data):
    value = data.get("tool_input")
    return value if isinstance(value, dict) else {}


def edited_text(data):
    """Text a Write/Edit/MultiEdit call introduces (new content only)."""
    ti = tool_input(data)
    parts = []
    if isinstance(ti.get("content"), str):
        parts.append(ti["content"])
    if isinstance(ti.get("new_string"), str):
        parts.append(ti["new_string"])
    for edit in ti.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            parts.append(edit["new_string"])
    return "\n".join(parts)


def run(main, name):
    try:
        data = read_input()
        main(data)
    except SystemExit:
        raise
    except HookError as exc:
        sys.stderr.write("%s: %s\n" % (name, exc))
        sys.exit(1)
    except Exception as exc:  # fail open, visibly
        sys.stderr.write("%s: internal error (%s); allowing the action\n" % (name, type(exc).__name__))
        sys.exit(1)
    sys.exit(0)

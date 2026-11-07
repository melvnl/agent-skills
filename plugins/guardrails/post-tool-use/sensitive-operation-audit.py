#!/usr/bin/env python3
"""sensitive-operation-audit: keep a local, redacted trail of sensitive actions the agent performed.

PostToolUse on Bash, Edit, Write and MultiEdit (runs after the tool succeeded). Appends one JSON line per
sensitive action to ${CLAUDE_PLUGIN_DATA}/audit.jsonl (mode 0600): git history and publishing commands,
migration and infrastructure commands, and edits to financial core, production configuration, or
migrations. Commands are stored with secrets and sensitive assignments redacted, truncated to 300 chars.
Silent; never blocks; skipped when CLAUDE_PLUGIN_DATA is unavailable.

This is a developer-side trail of agent activity, not a financial audit record (see the
financial-auditability skill for those).
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, patterns, shellparse  # noqa: E402

NAME = "sensitive-operation-audit"
GIT_SUBS = {"commit", "push", "reset", "rebase", "merge", "tag", "revert", "cherry-pick", "filter-branch", "filter-repo"}
INFRA = {"terraform": {"apply", "destroy", "import", "state"}, "kubectl": {"apply", "delete", "rollout", "scale", "patch"},
         "helm": {"install", "upgrade", "uninstall", "rollback"}}
MIGRATION_DEFAULTS = ["**/migrations/*.py", "**/migrations/*.sql", "**/alembic/versions/*.py", "**/db/migrate/*"]
ASSIGNMENT = re.compile(r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|KEY)[A-Z0-9_]*)=(\S+)")


def redact(command):
    for _, rx in patterns.SECRET_PATTERNS:
        command = rx.sub("[REDACTED]", command)
    command = ASSIGNMENT.sub(lambda m: m.group(1) + "=[REDACTED]", command)
    command = re.sub(r"(?i)(authorization:\s*(?:bearer|basic)\s+)\S+", r"\1[REDACTED]", command)
    command = re.sub(r"(?i)(--password[= ]|-p)(\S+)", r"\1[REDACTED]", command) if "mysql" in command else command
    return command[:300]


def bash_category(command):
    for toks in shellparse.simple_commands(command):
        cmd = toks[0]
        if cmd == "git":
            sub = next((t for t in toks[1:] if not t.startswith("-")), "")
            if sub in GIT_SUBS:
                return "git:" + sub
        if cmd in ("python", "python3") and "manage.py" in toks:
            i = toks.index("manage.py")
            if i + 1 < len(toks) and toks[i + 1] in ("migrate", "flush", "loaddata", "createsuperuser"):
                return "django:" + toks[i + 1]
        if cmd in ("alembic", "flyway") and any(t in ("upgrade", "downgrade", "migrate", "clean") for t in toks):
            return cmd + ":migrate"
        if cmd in INFRA and any(t in INFRA[cmd] for t in toks[1:3]):
            return cmd + ":" + next(t for t in toks[1:3] if t in INFRA[cmd])
        if cmd == "aws" and len(toks) > 2 and re.match(r"^(put|update|delete|create|terminate|modify|rm|rb|cp|sync)", toks[2]):
            return "aws:" + toks[1]
    return None


def main(data):
    data_dir = os.environ.get("CLAUDE_PLUGIN_DATA")
    project = hookio.project_dir(data)
    cfg = config.load(project)
    if not data_dir or not config.enabled(cfg, NAME):
        return
    tool, ti = data.get("tool_name"), hookio.tool_input(data)
    record = None
    if tool == "Bash":
        category = bash_category(ti.get("command", ""))
        if category:
            record = {"category": category, "command": redact(ti.get("command", ""))}
    elif tool in ("Edit", "Write", "MultiEdit"):
        path = ti.get("file_path", "")
        rel = config.relative(path, project) or os.path.basename(path)
        for category, globs in (("edit:financial_core", config.patterns(cfg, "financial_core")),
                                ("edit:production_config", config.patterns(cfg, "production_config")),
                                ("edit:migration", config.patterns(cfg, "migrations", MIGRATION_DEFAULTS))):
            if globs and path and config.matches(path, globs, project):
                record = {"category": category, "path": rel}
                break
    if not record:
        return
    record.update({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                   "session_id": data.get("session_id"), "project": os.path.basename(os.path.normpath(project)),
                   "tool": tool})
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "audit.jsonl")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


if __name__ == "__main__":
    hookio.run(main, NAME)

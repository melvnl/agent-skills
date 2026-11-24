#!/usr/bin/env python3
"""session-context-init: give a new or resumed session the code clarity rule and Software Factory state.

SessionStart hook. In every repository it adds the code clarity rule (turn off with "code-clarity" in
`disabled`). In repositories that use the Software Factory (`.factory/` or `tasks/STATUS.md` exists) it also
adds the session protocol reminder, a bounded snapshot of tasks/STATUS.md, git branch, uncommitted change
count and last commit, and which guardrail protections the project configured. After compaction it adds a
reminder to re-verify state from files, not memory. Read-only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, gitinfo, hookio  # noqa: E402

NAME = "session-context-init"
CLARITY = "code-clarity"
STATUS_LINES, STATUS_CHARS = 40, 3000
CLARITY_RULE = (
    "Code clarity: make code impossible to misunderstand instead of explaining it. Carry intent in names, types, "
    "named constants and small functions. Do not add comments or docstrings that restate what the code does, "
    "docstrings on private or self-explanatory functions, banner comments, or change-log comments. Comment only "
    "why: a non-obvious constraint, workaround, or requirement ID. Write the shortest direct code that handles "
    "the real cases: no checks for states that cannot occur, no single-use wrappers, no options nobody asked "
    "for. Leave existing comments alone unless the change touches the code they describe.")


def factory_context(data, project, cfg, status_path):
    parts = ["This repository uses the Software Factory. Follow the session protocol in CLAUDE.md, and route "
             "engineering requests through the factory-router skill."]
    if data.get("source") == "compact":
        parts.append("Context was just compacted: re-read tasks/STATUS.md and the active task file, and re-check "
                     "git status and the build before trusting remembered state (.factory/workflows/RESUME_WORK.md).")
    if gitinfo.is_repo(project):
        changes = gitinfo.status_lines(project) or []
        parts.append("Git: branch %s, %d uncommitted change(s), last commit: %s."
                     % (gitinfo.branch(project) or "?", len(changes), gitinfo.last_commit(project) or "none"))
    if os.path.isfile(status_path):
        with open(status_path, encoding="utf-8", errors="replace") as fh:
            snapshot = "".join(fh.readlines()[:STATUS_LINES])[:STATUS_CHARS]
        parts.append("tasks/STATUS.md (first %d lines; may be stale, verify against code):\n%s" % (STATUS_LINES, snapshot.rstrip()))
    protections = [k for k in ("financial_core", "production_config", "migrations", "protected_paths") if cfg.get(k)]
    if protections:
        parts.append("Guardrails configured for: %s (edits there ask for confirmation)." % ", ".join(protections))
    return parts


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    if not config.enabled(cfg, NAME):
        return
    status_path = os.path.join(project, "tasks", "STATUS.md")
    parts = [CLARITY_RULE] if config.enabled(cfg, CLARITY) else []
    if os.path.isdir(os.path.join(project, ".factory")) or os.path.isfile(status_path):
        parts += factory_context(data, project, cfg, status_path)
    if parts:
        hookio.add_context("SessionStart", "\n\n".join(parts))


if __name__ == "__main__":
    hookio.run(main, NAME)

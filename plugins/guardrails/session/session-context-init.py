#!/usr/bin/env python3
"""session-context-init: give a new or resumed session the Software Factory state, without narration.

SessionStart hook. Emits context only in repositories that use the Software Factory (`.factory/` or
`tasks/STATUS.md` exists): the session protocol reminder, a bounded snapshot of tasks/STATUS.md, git
branch, uncommitted change count and last commit, and which guardrail protections the project configured.
After compaction it adds a reminder to re-verify state from files, not memory. Read-only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, gitinfo, hookio  # noqa: E402

NAME = "session-context-init"
STATUS_LINES, STATUS_CHARS = 40, 3000


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    status_path = os.path.join(project, "tasks", "STATUS.md")
    if not config.enabled(cfg, NAME) or not (os.path.isdir(os.path.join(project, ".factory")) or os.path.isfile(status_path)):
        return
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
    hookio.add_context("SessionStart", "\n\n".join(parts))


if __name__ == "__main__":
    hookio.run(main, NAME)

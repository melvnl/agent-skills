#!/usr/bin/env python3
"""protect-database-migrations: ask before editing a migration that is already committed.

PreToolUse on Edit, Write and MultiEdit. Migrations that exist in HEAD may already have run somewhere;
editing them makes environments diverge silently. New (uncommitted) migrations are free to edit. Paths
come from `migrations` globs in .claude/guardrails.json, defaulting to common layouts.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, gitinfo, hookio  # noqa: E402

NAME = "protect-database-migrations"
DEFAULT_GLOBS = ["**/migrations/*.py", "**/migrations/*.sql", "**/migrations/versions/*.py",
                 "**/db/migrate/*", "**/alembic/versions/*.py", "**/flyway/*.sql"]


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit") or not path or not config.enabled(cfg, NAME):
        return
    if os.path.basename(path) == "__init__.py":
        return
    globs = config.patterns(cfg, "migrations", DEFAULT_GLOBS)
    rel = config.relative(path, project)
    if rel and config.matches(path, globs, project) and gitinfo.is_tracked_in_head(project, rel):
        hookio.ask("%s: %s is a committed migration and may already be applied in some environment. Add a new "
                   "migration instead of editing it, unless you are certain it has never run anywhere." % (NAME, rel))


if __name__ == "__main__":
    hookio.run(main, NAME)

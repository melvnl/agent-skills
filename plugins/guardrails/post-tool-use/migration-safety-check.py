#!/usr/bin/env python3
"""migration-safety-check: flag destructive or locking operations in edited migration files.

PostToolUse on Write, Edit and MultiEdit, for paths matching `migrations` globs (same defaults as
protect-database-migrations). Scans the text the edit introduced for Django operations (RemoveField,
DeleteModel, RenameField, RenameModel, AlterField, NOT NULL AddField without default, RunPython without a
reverse, RunSQL with destructive SQL) and raw SQL (DROP, TRUNCATE, RENAME, MODIFY/CHANGE COLUMN, NOT NULL
ADD COLUMN without DEFAULT, CREATE INDEX). Feedback only: the database-migrations skill and workflow decide.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, pyscan  # noqa: E402

NAME = "migration-safety-check"
DEFAULT_GLOBS = ["**/migrations/*.py", "**/migrations/*.sql", "**/migrations/versions/*.py",
                 "**/db/migrate/*", "**/alembic/versions/*.py", "**/flyway/*.sql"]
DJANGO = {
    "RemoveField": "drops a column (data loss; old code still reading it breaks during deploy)",
    "DeleteModel": "drops a table (data loss)",
    "RenameField": "renames a column (running old code breaks; use expand-migrate-contract)",
    "RenameModel": "renames a table (running old code breaks)",
    "AlterField": "may rewrite or lock the table, or narrow the column",
}
SQL = [
    (re.compile(r"(?i)\bdrop\s+(table|column|index|database|schema)\b"), "DROP (data or index loss)"),
    (re.compile(r"(?i)\btruncate\b"), "TRUNCATE (data loss)"),
    (re.compile(r"(?i)\brename\s+(table|column|to)\b"), "RENAME (running old code breaks)"),
    (re.compile(r"(?i)\b(modify|change)\s+(column\s+)?\w+\s+\w+"), "MODIFY/CHANGE COLUMN (type change, rebuild or lock)"),
    (re.compile(r"(?i)\badd\s+(column\s+)?\w+\s+[\w()]+(?:(?!default)[^,;])*\bnot\s+null\b(?:(?!default)[^,;])*(,|;|$)"),
     "NOT NULL column without DEFAULT (fails on existing rows or rewrites the table)"),
    (re.compile(r"(?i)\bcreate\s+(unique\s+)?index\b"), "CREATE INDEX (check online DDL on large tables)"),
]


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not path or not config.enabled(cfg, NAME):
        return
    if not config.matches(path, config.patterns(cfg, "migrations", DEFAULT_GLOBS), project):
        return
    rel = config.relative(path, project) or os.path.basename(path)
    lines = hookio.introduced_lines(data)
    issues = []
    for op, why in DJANGO.items():
        for lineno, _ in pyscan.calls(lines, re.compile(r"\b%s\s*\(" % op)):
            issues.append("%s:%s %s %s" % (rel, lineno, op, why))
    for lineno, call in pyscan.calls(lines, re.compile(r"\bAddField\s*\(")):
        if "null=True" not in call.replace(" ", "") and "default=" not in call:
            issues.append("%s:%s AddField NOT NULL without default (fails or rewrites on existing rows)" % (rel, lineno))
    for lineno, call in pyscan.calls(lines, re.compile(r"\bRunPython\s*\(")):
        args = pyscan.strip_strings(call)[call.index("(") + 1:]
        if "reverse_code" not in args and args.count(",") == 0:
            issues.append("%s:%s RunPython without a reverse function (use RunPython.noop with a reason if irreversible)" % (rel, lineno))
    for lineno, text in lines:
        for rx, why in SQL:
            if rx.search(text):
                issues.append("%s:%s %s" % (rel, lineno, why))
                break
    if issues:
        hookio.feedback("%s: %s. Use expand-migrate-contract across deploys, batch backfills, name the DDL "
                        "algorithm or online tool for large tables, rehearse on realistic data, and get approval for "
                        "destructive steps (DATABASE_MIGRATION workflow)." % (NAME, "; ".join(sorted(set(issues))[:8])), limit=1500)


if __name__ == "__main__":
    hookio.run(main, NAME)

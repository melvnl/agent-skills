#!/usr/bin/env python3
"""format-after-edit: run the project's formatter on an edited file and tell Claude when it changed.

PostToolUse on Write, Edit and MultiEdit. Runs only when the user enabled the plugin option
`run_project_commands`. Uses `commands.format` from .claude/guardrails.json when it applies to the file;
otherwise auto-detects the project's own ruff, biome, prettier or gofmt (lib/detect.py). When no formatter
can run for the file, says so once per session. A reformatted file means Claude's view of it is stale, so
the hook adds context asking to re-read it before the next edit. Formatter failures are fed back.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commands, config, hookio  # noqa: E402

NAME = "format-after-edit"


def digest(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def main(data):
    step = commands.plan(data, "format", NAME, 30)
    if step is None:
        return
    if step[0] == "skip":
        commands.mention_skip(data, step[1], "format", NAME)
        return
    project = hookio.project_dir(data)
    path = step[2]
    before = digest(path)
    code, output, _ = commands.execute(step, project)
    rel = config.relative(path, project) or path
    if code != 0:
        status = output if code is None else "exit %s" % code
        hookio.feedback("%s: formatter failed on %s (%s):\n%s" % (NAME, rel, status, commands.tail(output, 800)), limit=1200)
    if digest(path) != before:
        hookio.add_context("PostToolUse", "%s: %s was reformatted by the project formatter. Re-read it before "
                                          "editing it again." % (NAME, rel))


if __name__ == "__main__":
    hookio.run(main, NAME)

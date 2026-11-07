#!/usr/bin/env python3
"""format-after-edit: run the project's formatter on an edited file and tell Claude when it changed.

PostToolUse on Write, Edit and MultiEdit. Runs only when the user enabled the plugin option
`run_project_commands` and the project configures `commands.format` in .claude/guardrails.json
(e.g. "ruff format {files}"). Never guesses a tool. A reformatted file means Claude's view of it is
stale, so the hook adds context asking to re-read it before the next edit. Formatter failures are fed back.
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
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not commands.allowed():
        return
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    command_spec = commands.spec(cfg, "format", 30)
    if not config.enabled(cfg, NAME) or not command_spec or not path or not commands.applies(command_spec, path, project):
        return
    before = digest(path)
    code, output = commands.run(command_spec, [path], project)
    rel = config.relative(path, project) or path
    if code != 0:
        status = output if code is None else "exit %s" % code
        hookio.feedback("%s: formatter failed on %s (%s):\n%s" % (NAME, rel, status, commands.tail(output, 800)), limit=1200)
    if digest(path) != before:
        hookio.add_context("PostToolUse", "%s: %s was reformatted by the project formatter. Re-read it before "
                                          "editing it again." % (NAME, rel))


if __name__ == "__main__":
    hookio.run(main, NAME)

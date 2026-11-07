#!/usr/bin/env python3
"""typecheck-after-edit: run the project's typecheck command on an edited file and feed back problems.

PostToolUse on Write, Edit and MultiEdit. Runs only when the user enabled the plugin option
`run_project_commands` and the project configures `commands.typecheck` in .claude/guardrails.json, for
files matching its optional `files` globs. Never guesses a tool. Timeouts are reported, never passed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commands, hookio  # noqa: E402

NAME = "typecheck-after-edit"


def main(data):
    commands.post_edit_check(data, "typecheck", NAME, 120, "the type checker")


if __name__ == "__main__":
    hookio.run(main, NAME)

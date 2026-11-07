#!/usr/bin/env python3
"""lint-after-edit: run the project's lint command on an edited file and feed back problems.

PostToolUse on Write, Edit and MultiEdit. Runs only when the user enabled the plugin option
`run_project_commands` and the project configures `commands.lint` in .claude/guardrails.json, for
files matching its optional `files` globs. Never guesses a tool. Timeouts are reported, never passed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commands, hookio  # noqa: E402

NAME = "lint-after-edit"


def main(data):
    commands.post_edit_check(data, "lint", NAME, 60, "the linter")


if __name__ == "__main__":
    hookio.run(main, NAME)

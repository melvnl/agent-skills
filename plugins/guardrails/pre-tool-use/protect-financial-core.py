#!/usr/bin/env python3
"""protect-financial-core: ask before editing files the project declares as financial core.

PreToolUse on Edit, Write and MultiEdit. Active only for paths matching `financial_core` globs in
.claude/guardrails.json (no defaults: only the project knows which code decides credit, limits or money).
Asking keeps a human aware that decision logic, thresholds or monetary computation is changing, and points
to the Software Factory fintech overlay gates.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio  # noqa: E402

NAME = "protect-financial-core"


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    globs = config.patterns(cfg, "financial_core")
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit") or not globs or not config.enabled(cfg, NAME):
        return
    if path and config.matches(path, globs, project):
        rel = config.relative(path, project) or path
        hookio.ask("%s: %s is financial core (credit, limits or money logic). Confirm the change is within an "
                   "approved spec; the fintech overlay requires domain and invariant review and golden-set checks "
                   "before merge." % (NAME, rel))


if __name__ == "__main__":
    hookio.run(main, NAME)

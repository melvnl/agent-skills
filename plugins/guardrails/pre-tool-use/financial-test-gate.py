#!/usr/bin/env python3
"""financial-test-gate: deny commits that change financial core code without changing any test.

PreToolUse on Bash. For each `git commit` in the command, compares the files being committed (staged,
plus modified tracked files for -a/--all) with the project's `financial_core` globs and test globs
(`test_paths`, default common Python/JS test layouts). Core changes with no test change are denied:
financial logic changes need tests that pin the new behavior. Inactive without `financial_core`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, gitinfo, hookio, shellparse  # noqa: E402

NAME = "financial-test-gate"
DEFAULT_TEST_GLOBS = ["**/test_*.py", "**/*_test.py", "**/tests/**", "**/test/**", "**/*.test.*", "**/*.spec.*",
                      "**/__tests__/**"]


def commit_flags(toks):
    """Return flags of a `git commit` simple command, or None if it isn't one."""
    if toks[0] != "git":
        return None
    rest, i = toks[1:], 0
    while i < len(rest) and rest[i].startswith("-"):
        i += 2 if rest[i] in ("-C", "-c") else 1
    if i >= len(rest) or rest[i] != "commit":
        return None
    return [t for t in rest[i + 1:] if t.startswith("-")]


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    core_globs = config.patterns(cfg, "financial_core")
    if data.get("tool_name") != "Bash" or not core_globs or not config.enabled(cfg, NAME):
        return
    for toks in shellparse.simple_commands(hookio.tool_input(data).get("command", "")):
        flags = commit_flags(toks)
        if flags is None or "--dry-run" in flags:
            continue
        files = set(gitinfo.staged_files(project) or [])
        if "--all" in flags or any(f.startswith("-") and not f.startswith("--") and "a" in f[1:] for f in flags):
            files |= set(gitinfo.modified_tracked_files(project) or [])
        test_globs = config.patterns(cfg, "test_paths", DEFAULT_TEST_GLOBS)
        core = sorted(f for f in files if config.matches(os.path.join(project, f), core_globs, project))
        tests = [f for f in files if config.matches(os.path.join(project, f), test_globs, project)]
        if core and not tests:
            hookio.deny("%s: this commit changes financial core (%s) without changing any test. Add or update the "
                        "tests that pin the new behavior (boundaries, golden cases) in the same commit, or ask the "
                        "user to approve committing without them." % (NAME, ", ".join(core[:5])))


if __name__ == "__main__":
    hookio.run(main, NAME)

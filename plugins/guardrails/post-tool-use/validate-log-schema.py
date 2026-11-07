#!/usr/bin/env python3
"""validate-log-schema: enforce the project's structured-logging shape on new log calls, where configured.

PostToolUse on Write, Edit and MultiEdit of Python files. Active only when the project sets
`logging.event_name_pattern` in .claude/guardrails.json (e.g. "^[a-z][a-z0-9_]*$"). For each log call the
edit introduces: the first argument must be a constant string matching the pattern; f-strings, string
concatenation and %-formatting of the message are flagged (variable data belongs in fields).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, patterns, pyscan  # noqa: E402

NAME = "validate-log-schema"
FIRST_ARG = re.compile(r"""\(\s*(?P<prefix>[rbuRBUfF]{0,2})(?P<q>['"])(?P<msg>(?:\\.|(?!(?P=q)).)*)(?P=q)\s*(?P<after>[,)%+.]?)""", re.S)


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    pattern = (cfg.get("logging") or {}).get("event_name_pattern")
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not path.endswith(".py") or not pattern:
        return
    if not config.enabled(cfg, NAME):
        return
    event_rx = re.compile(pattern)
    rel = config.relative(path, project) or os.path.basename(path)
    issues = []
    for lineno, call in pyscan.calls(hookio.introduced_lines(data), re.compile(patterns.LOG_CALL.pattern)):
        m = FIRST_ARG.search(call)
        if not m:
            issues.append("%s:%s message is not a constant string" % (rel, lineno))
        elif "f" in m.group("prefix").lower():
            issues.append("%s:%s f-string message" % (rel, lineno))
        elif m.group("after") in ("%", "+", "."):
            issues.append("%s:%s message built by formatting or concatenation" % (rel, lineno))
        elif not event_rx.search(m.group("msg")):
            issues.append("%s:%s event '%s' doesn't match %s" % (rel, lineno, m.group("msg")[:60], pattern))
    if issues:
        hookio.feedback("%s: %s. Use a constant event name matching the project pattern and put variable data "
                        "in structured fields." % (NAME, "; ".join(issues[:6])), limit=1200)


if __name__ == "__main__":
    hookio.run(main, NAME)

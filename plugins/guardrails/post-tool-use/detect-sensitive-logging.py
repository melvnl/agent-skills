#!/usr/bin/env python3
"""detect-sensitive-logging: flag log calls that may write secrets, personal data, or whole payloads.

PostToolUse on Write, Edit and MultiEdit of Python files. For each log call the edit introduces, checks
field names, dict keys, keyword arguments and f-string expressions (not the words of a log message) for
sensitive names (password, token, authorization, national id, email, phone, card or account numbers, ...),
and flags whole-object logging (request.headers/body/data, vars(), __dict__). Feedback only: deciding
what is safe is a judgment for the logging-security-and-redaction skill and reviewers.
Config: `disabled: ["detect-sensitive-logging"]`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, patterns, pyscan  # noqa: E402

NAME = "detect-sensitive-logging"
LOG_START = re.compile(patterns.LOG_CALL.pattern)
BENIGN = re.compile(r"(?i)^(has|is|num|n|count|total)_|_(count|present|verified|masked|hash|hashed|ref|domain|country|"
                    r"type|length|len|status|required|enabled|changed|reset|expired|valid|exists)$")


def findings_for(call):
    found = set()
    for name in pyscan.identifiers(call):
        if patterns.SENSITIVE_KEY.search(name) and not BENIGN.search(name):
            found.add("`%s`" % name)
    scan = pyscan.strip_strings(call) + " " + " ".join(pyscan.fstring_expressions(call))
    m = patterns.WHOLE_OBJECT.search(scan)
    if m:
        obj = m.group(0).strip(" ,}")
        while obj.endswith(")") and obj.count("(") < obj.count(")"):
            obj = obj[:-1].rstrip(" ,")
        found.add("whole object `%s`" % obj)
    return sorted(found)


def main(data):
    project = hookio.project_dir(data)
    path = hookio.tool_input(data).get("file_path", "")
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not path.endswith(".py"):
        return
    if not config.enabled(config.load(project), NAME):
        return
    rel = config.relative(path, project) or os.path.basename(path)
    report = []
    for lineno, call in pyscan.calls(hookio.introduced_lines(data), LOG_START):
        items = findings_for(call)
        if items:
            report.append("%s:%s %s" % (rel, lineno, ", ".join(items)))
    if report:
        hookio.feedback(
            "%s: log calls may expose sensitive data: %s. Log explicit, allowlisted fields only: never secrets or "
            "auth headers; raw identity, contact or financial identifiers only as approved internal references "
            "or keyed pseudonyms; no whole requests, bodies, headers or objects. If a flagged name is not "
            "sensitive, say why." % (NAME, "; ".join(report[:6])), limit=1200)


if __name__ == "__main__":
    hookio.run(main, NAME)

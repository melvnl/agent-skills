#!/usr/bin/env python3
"""detect-hardcoded-credentials: flag credential-named variables assigned string literals in source code.

PostToolUse on Write, Edit and MultiEdit. Complements detect-secret-exposure (known token formats) by
catching `password = "hunter22"`-style assignments that have no recognizable format. Feedback only (the
edit stays; Claude must address it). Skips test paths, example/template files, placeholders, and values
equal to the variable's own name (field-name constants).
Config: `disabled: ["detect-hardcoded-credentials"]`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, patterns  # noqa: E402

NAME = "detect-hardcoded-credentials"
ASSIGN = re.compile(
    r"""(?ix)\b((?:[a-z_]\w*?)?(?:password|passwd|pwd|secret|api_?key|access_?key|private_?key|client_?secret|
    auth_?token|access_?token|refresh_?token|signing_?key|token)\w*)['"]?\s*
    (?::\s*[\w\[\]\x20,.|]+?\s*=|[:=])\s*[rbuf]?(['"])([^'"\s]{6,})\2"""
)
SKIP_PATH = re.compile(r"(^|/)(tests?|fixtures?|__tests__|spec)/|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(example|sample|template|md|rst|txt)$")
NOT_SECRET_VALUE = re.compile(r"(?i)^(true|false|none|null|bearer|basic|token|password|secret|required|optional)$")


def main(data):
    project = hookio.project_dir(data)
    if not config.enabled(config.load(project), NAME) or data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return
    path = hookio.tool_input(data).get("file_path", "")
    rel = config.relative(path, project) or os.path.basename(path)
    if not path or SKIP_PATH.search(rel):
        return
    findings = []
    for lineno, line in hookio.introduced_lines(data):
        for m in ASSIGN.finditer(line):
            name, value = m.group(1), m.group(3)
            if patterns.PLACEHOLDER.search(value) or NOT_SECRET_VALUE.match(value) or value.lower() == name.lower():
                continue
            findings.append(f"{rel}:{lineno} `{name}`")
    if findings:
        hookio.feedback(
            f"{NAME}: possible hard-coded credentials: {', '.join(findings[:5])}. Load credentials from the "
            "environment or the secret manager (and document the variable in .env.example). If a value is not a "
            "credential, rename the variable or confirm it to the user; if it is a real secret, tell the user so "
            "it can be rotated."
        )


if __name__ == "__main__":
    hookio.run(main, NAME)

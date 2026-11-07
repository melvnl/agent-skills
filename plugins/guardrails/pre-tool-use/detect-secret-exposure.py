#!/usr/bin/env python3
"""detect-secret-exposure: deny writes and commands that contain high-confidence secret formats.

PreToolUse on Write, Edit, MultiEdit and Bash. Checks only the text being introduced (new content,
new_string, the command), against known token formats (AWS keys, private key blocks, GitHub, Slack,
Stripe, Google keys, JWTs, credentials in URLs). Obvious placeholders (EXAMPLE, changeme, ${VAR}) pass.
The reason names the pattern and line, never the value.
Config: `disabled: ["detect-secret-exposure"]`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, patterns  # noqa: E402

NAME = "detect-secret-exposure"


def main(data):
    project = hookio.project_dir(data)
    if not config.enabled(config.load(project), NAME):
        return
    tool, ti = data.get("tool_name"), hookio.tool_input(data)
    if tool == "Bash":
        text, where = ti.get("command", ""), "the command"
    elif tool in ("Write", "Edit", "MultiEdit"):
        text, where = hookio.edited_text(data), os.path.basename(ti.get("file_path", "")) or "the edit"
    else:
        return
    hits = list(patterns.find_secrets(text))
    if hits:
        found = ", ".join(f"{name} (line {line})" for name, line in hits[:5])
        hookio.deny(
            f"{NAME}: {where} contains what looks like a real secret: {found}. Secrets must not be written to "
            "files, commands, or the conversation. Read it from the environment or the secret manager instead; "
            "for tests, use an obviously fake value (e.g. containing EXAMPLE). If a real secret was exposed, "
            "tell the user so it can be rotated."
        )


if __name__ == "__main__":
    hookio.run(main, NAME)

#!/usr/bin/env python3
"""protect-sensitive-files: deny reading or writing secret-bearing files (.env, keys, credential stores).

PreToolUse on Read, Edit, Write, MultiEdit, Grep, and Bash. For Bash, the command is parsed into simple
commands and every path-like argument is checked, so `cat .env` and `cp .env /tmp` are caught while
`grep TODO src/` is not. Templates such as `.env.example` stay allowed.
Config: `protected_paths` (extra globs), `disabled: ["protect-sensitive-files"]`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, shellparse  # noqa: E402

NAME = "protect-sensitive-files"
DEFAULT_GLOBS = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.kdbx", "id_rsa", "id_rsa.*",
                 "id_ecdsa", "id_ecdsa.*", "id_ed25519", "id_ed25519.*", ".netrc", ".pypirc", "**/.aws/credentials",
                 "**/.ssh/*", "*.tfstate", "*.tfstate.*"]
ALLOWED_SUFFIXES = (".example", ".sample", ".template", ".dist", ".pub")
FILE_TOOLS = {"Read": "file_path", "Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path", "Grep": "path"}


def is_protected(path, globs, project):
    if not path or os.path.basename(path).endswith(ALLOWED_SUFFIXES):
        return False
    return config.matches(path, globs, project)


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    if not config.enabled(cfg, NAME):
        return
    globs = DEFAULT_GLOBS + config.patterns(cfg, "protected_paths")
    tool, ti = data.get("tool_name"), hookio.tool_input(data)
    candidates = []
    if tool in FILE_TOOLS:
        candidates.append(ti.get(FILE_TOOLS[tool]) or "")
    elif tool == "Bash":
        for toks in shellparse.simple_commands(ti.get("command", "")):
            candidates.extend(t for t in toks[1:] if not t.startswith("-") and t != "__SUBST__")
            # redirections such as `>.env` or `<.env` arrive attached to the token
            candidates.extend(t.lstrip("<>") for t in toks[1:] if t[:1] in "<>")
    for path in candidates:
        if is_protected(path, globs, project):
            hookio.deny(
                f"{os.path.basename(path)} is a protected secrets file ({NAME}). Its contents must not enter the "
                "conversation, logs or commits. Use the template (e.g. .env.example) for variable names, or ask "
                "the user to provide the specific non-secret value you need."
            )


if __name__ == "__main__":
    hookio.run(main, NAME)

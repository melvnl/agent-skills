#!/usr/bin/env python3
"""verify-before-stop: run the project's verification command before Claude finishes, once.

Stop hook. Runs only when the user enabled `run_project_commands`, the project configures
`commands.verify` (e.g. "make test"), and the git working tree has changes (nothing to verify otherwise).
On failure it blocks the stop once with the output tail; `stop_hook_active` prevents loops, so a second
stop is always allowed. A timeout is reported as a failure, never as a pass.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commands, config, gitinfo, hookio  # noqa: E402

NAME = "verify-before-stop"
MAX_TIMEOUT_S = 540


def main(data):
    if data.get("stop_hook_active") or not commands.allowed():
        return
    project = hookio.project_dir(data)
    cfg = config.load(project)
    command_spec = commands.spec(cfg, "verify", 300)
    if not config.enabled(cfg, NAME) or not command_spec:
        return
    if gitinfo.is_repo(project) and not gitinfo.status_lines(project):
        return
    command_spec["timeout"] = min(command_spec["timeout"], MAX_TIMEOUT_S)
    command_spec["run"] = command_spec["run"].replace("{files}", "")
    code, output = commands.run(command_spec, [], project)
    if code == 0:
        return
    status = output if code is None else "exit %s" % code
    hookio.feedback("%s: the project's verification command failed (%s):\n%s\nFix the failures before finishing, "
                    "or report them to the user as unresolved." % (NAME, status, commands.tail(output)), limit=1800)


if __name__ == "__main__":
    hookio.run(main, NAME)

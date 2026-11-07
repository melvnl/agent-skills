"""Run project-defined check commands (format, lint, typecheck, verify) from guardrails.json.

Commands come from the repository, so they run only when the user opted in through the plugin option
`run_project_commands` (exported by Claude Code as CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS).
GUARDRAILS_RUN_PROJECT_COMMANDS=1 is accepted as an explicit local override (used by tests).

Config shape: "commands": {"lint": "ruff check {files}"} or
              "commands": {"lint": {"run": "ruff check {files}", "files": ["**/*.py"], "timeout": 60}}
`{files}` expands to the shell-quoted edited paths, relative to the project root.
"""
import os
import shlex
import subprocess

from lib import config

TRUTHY = {"1", "true", "yes", "on"}


def allowed():
    value = os.environ.get("CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS") or os.environ.get("GUARDRAILS_RUN_PROJECT_COMMANDS", "")
    return value.strip().lower() in TRUTHY


def spec(cfg, kind, default_timeout):
    raw = (cfg.get("commands") or {}).get(kind)
    if isinstance(raw, str):
        return {"run": raw, "files": None, "timeout": default_timeout}
    if isinstance(raw, dict) and isinstance(raw.get("run"), str):
        files = raw.get("files")
        return {"run": raw["run"], "files": files if isinstance(files, list) else None,
                "timeout": int(raw.get("timeout", default_timeout))}
    return None


def applies(command_spec, path, project):
    globs = command_spec.get("files")
    return True if not globs else config.matches(path, globs, project)


def run(command_spec, files, project):
    rel_files = [config.relative(f, project) or f for f in files]
    cmd = command_spec["run"].replace("{files}", " ".join(shlex.quote(f) for f in rel_files))
    try:
        proc = subprocess.run(cmd, shell=True, cwd=project, capture_output=True, text=True,
                              timeout=command_spec["timeout"])
    except subprocess.TimeoutExpired:
        return None, "timed out after %ss" % command_spec["timeout"]
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def tail(text, limit=1400):
    text = text.strip()
    return text if len(text) <= limit else "...\n" + text[-limit:]


def post_edit_check(data, kind, name, default_timeout, what):
    """Shared PostToolUse body for lint/typecheck: run the configured command on the edited file and feed
    failures back. Returns silently when not opted in, not configured, or not applicable."""
    from lib import hookio
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not allowed():
        return
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    command_spec = spec(cfg, kind, default_timeout)
    if not config.enabled(cfg, name) or not command_spec or not path or not applies(command_spec, path, project):
        return
    code, output = run(command_spec, [path], project)
    if code == 0:
        return
    status = output if code is None else "exit %s" % code
    hookio.feedback("%s: %s reported problems in %s (%s):\n%s\nFix them, or explain why they are out of scope."
                    % (name, what, config.relative(path, project) or path, status, tail(output)), limit=1800)

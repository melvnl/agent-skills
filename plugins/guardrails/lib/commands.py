"""Run project-defined check commands (format, lint, typecheck, verify) from guardrails.json.

Commands come from the repository, so they run only when the user opted in through the plugin option
`run_project_commands` (exported by Claude Code as CLAUDE_PLUGIN_OPTION_RUN_PROJECT_COMMANDS).
GUARDRAILS_RUN_PROJECT_COMMANDS=1 is accepted as an explicit local override (used by tests).

Config shape: "commands": {"lint": "ruff check {files}"} or
              "commands": {"lint": {"run": "ruff check {files}", "files": ["**/*.py"], "timeout": 60}}
`{files}` expands to the shell-quoted edited paths, relative to the project root.

Without a configured command, format and lint fall back to lib/detect (the project's own ruff, biome,
eslint, prettier or gofmt), unless the project sets "auto_detect": false. A check that can't run (unknown
file type, tool not configured or not installed) is mentioned once per session to Claude and the user.
"""
import os
import shlex
import subprocess

from lib import config, detect, notices

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


def run_argv(result, timeout):
    """Run an auto-detected tool: fixed argv, no shell, from the directory holding its config."""
    try:
        proc = subprocess.run(result["argv"], cwd=result["cwd"], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timed out after %ss" % timeout
    except OSError as exc:
        return 127, "could not start %s: %s" % (result["label"], exc.strerror or exc)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def plan(data, kind, name, default_timeout, autodetect=True):
    """What a post-edit hook should do for the edited file:
    None (nothing), ("shell", spec, path), ("argv", result, path) or ("skip", result, path)."""
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not allowed():
        return None
    from lib import hookio
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    if not path or not config.enabled(cfg, name):
        return None
    command_spec = spec(cfg, kind, default_timeout)
    if command_spec and applies(command_spec, path, project):
        return "shell", command_spec, path
    if not autodetect or cfg.get("auto_detect") is False:
        return None
    result = detect.detect(path, project, kind)
    if result is None:
        return None
    result["timeout"] = command_spec["timeout"] if command_spec else default_timeout
    return ("argv" if result.found else "skip"), result, path


def execute(step, project):
    """Run a planned shell or argv step: (exit code or None on timeout, output, what ran)."""
    mode, item, path = step
    if mode == "shell":
        code, output = run(item, [path], project)
        return code, output, "the configured command"
    code, output = run_argv(item, item["timeout"])
    return code, output, item["label"]


def mention_skip(data, result, kind, name):
    """Tell Claude and the user, once per session, that a check was skipped and why."""
    from lib import hookio
    if not notices.claim(data, result["key"]):
        return
    if result["key"].startswith("type:"):
        text = ("Guardrails: %s, so format and lint checks are skipped for them. To check them, set "
                "commands.format / commands.lint in .claude/guardrails.json." % result["skip"])
    else:
        text = "Guardrails (%s): %s, so %s checks are skipped for these files." % (name, result["skip"], kind)
    hookio.notify("PostToolUse", text)


def tail(text, limit=1400):
    text = text.strip()
    return text if len(text) <= limit else "...\n" + text[-limit:]


def post_edit_check(data, kind, name, default_timeout, what, autodetect=False):
    """Shared PostToolUse body for lint/typecheck: run the configured (or, with autodetect, detected) command
    on the edited file and feed failures back. Silent when not opted in or nothing applies; a skipped
    auto-detection is mentioned once per session."""
    from lib import hookio
    step = plan(data, kind, name, default_timeout, autodetect)
    if step is None:
        return
    if step[0] == "skip":
        mention_skip(data, step[1], kind, name)
        return
    project = hookio.project_dir(data)
    code, output, ran = execute(step, project)
    if code == 0:
        return
    status = output if code is None else "exit %s" % code
    hookio.feedback("%s: %s (%s) reported problems in %s (%s):\n%s\nFix them, or explain why they are out of scope."
                    % (name, what, ran, config.relative(step[2], project) or step[2], status, tail(output)), limit=1800)

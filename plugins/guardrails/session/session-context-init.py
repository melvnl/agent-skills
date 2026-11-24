#!/usr/bin/env python3
"""session-context-init: give a new or resumed session the code clarity rule and Software Factory state.

SessionStart hook. In every repository it adds the code clarity rule (turn off with "code-clarity" in
`disabled`). In repositories that use the Software Factory (`.factory/` or `tasks/status.md` exists; the
pre-rename name `tasks/STATUS.md` is read too) it also
adds the session protocol reminder, a bounded snapshot of tasks/status.md, git branch, uncommitted change
count and last commit, and which guardrail protections the project configured. After compaction it adds a
reminder to re-verify state from files, not memory. It also reports, to Claude and the user, which formatter
and linter the post-edit hooks will run per project folder and which checks will be skipped and why.
Read-only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import commands, config, detect, gitinfo, hookio, notices  # noqa: E402

NAME = "session-context-init"
CLARITY = "code-clarity"
STATUS_LINES, STATUS_CHARS = 40, 3000
CLARITY_RULE = (
    "Code clarity: make code impossible to misunderstand instead of explaining it. Carry intent in names, types, "
    "named constants and small functions. Do not add comments or docstrings that restate what the code does, "
    "docstrings on private or self-explanatory functions, banner comments, or change-log comments. Comment only "
    "why: a non-obvious constraint, workaround, or requirement ID. Write the shortest direct code that handles "
    "the real cases: no checks for states that cannot occur, no single-use wrappers, no options nobody asked "
    "for. Leave existing comments alone unless the change touches the code they describe.")


PROBE_EXT = {"python": ".py", "js": ".ts", "go": ".go"}
KIND_HOOKS = (("format", "format-after-edit"), ("lint", "lint-after-edit"))
ENABLE = "claude plugin configure engineering-guardrails@melvin-skills"


def toolchain_summary(data, project, cfg):
    """One line per project folder: what format/lint will run after edits, or why it is skipped."""
    kinds = [kind for kind, hook in KIND_HOOKS if config.enabled(cfg, hook)]
    if not kinds or cfg.get("auto_detect") is False:
        return None
    allowed, lines, found_any = commands.allowed(), [], False
    for folder, fam in detect.project_roots(project):
        probe = os.path.join(folder, "probe" + PROBE_EXT[fam])
        parts = []
        for kind in kinds:
            spec = commands.spec(cfg, kind, 0)
            if spec and commands.applies(spec, probe, project):
                parts.append("%s: configured command" % kind)
                found_any = True
                continue
            result = detect.detect(probe, project, kind)
            if result is None:
                continue
            if result.found:
                parts.append("%s: %s" % (kind, result["label"]))
                found_any = True
            else:
                parts.append("%s: skipped, %s" % (kind, result["skip"]))
                if allowed:
                    notices.claim(data, result["key"])  # already said here; edits don't repeat it
        rel = os.path.relpath(folder, os.path.realpath(project)).replace(os.sep, "/")
        lines.append("- %s (%s): %s" % (rel, detect.LABELS[fam], "; ".join(parts)))
    if not allowed:
        if not found_any:
            return None
        return ("Guardrails: format/lint after edits is off because run_project_commands is disabled. "
                "It would run:\n%s\nEnable it with `%s`." % ("\n".join(lines), ENABLE))
    if not lines:
        return ("Guardrails: no Python, JavaScript/TypeScript or Go project found, so format and lint checks after "
                "edits are skipped. Set commands.format / commands.lint in .claude/guardrails.json to add them.")
    return "Guardrails: format and lint after each edit:\n" + "\n".join(lines)


def find_status(project):
    """tasks/status.md, or tasks/STATUS.md in repositories set up before the factory used lowercase names."""
    tasks = os.path.join(project, "tasks")
    try:
        entries = set(os.listdir(tasks))
    except OSError:
        return None
    for name in ("status.md", "STATUS.md"):  # exact names: macOS file systems ignore case
        if name in entries:
            return os.path.join(tasks, name)
    return None


def factory_context(data, project, cfg, status_path):
    parts = ["This repository uses the Software Factory. Follow the session protocol in CLAUDE.md, and route "
             "engineering requests through the factory-router skill."]
    if data.get("source") == "compact":
        parts.append("Context was just compacted: re-read tasks/status.md and the active task file, and re-check "
                     "git status and the build before trusting remembered state (.factory/workflows/resume-work.md).")
    if gitinfo.is_repo(project):
        changes = gitinfo.status_lines(project) or []
        parts.append("Git: branch %s, %d uncommitted change(s), last commit: %s."
                     % (gitinfo.branch(project) or "?", len(changes), gitinfo.last_commit(project) or "none"))
    if status_path:
        with open(status_path, encoding="utf-8", errors="replace") as fh:
            snapshot = "".join(fh.readlines()[:STATUS_LINES])[:STATUS_CHARS]
        parts.append("tasks/%s (first %d lines; may be stale, verify against code):\n%s"
                     % (os.path.basename(status_path), STATUS_LINES, snapshot.rstrip()))
    protections = [k for k in ("financial_core", "production_config", "migrations", "protected_paths") if cfg.get(k)]
    if protections:
        parts.append("Guardrails configured for: %s (edits there ask for confirmation)." % ", ".join(protections))
    return parts


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    if not config.enabled(cfg, NAME):
        return
    status_path = find_status(project)
    parts = [CLARITY_RULE] if config.enabled(cfg, CLARITY) else []
    if os.path.isdir(os.path.join(project, ".factory")) or status_path:
        parts += factory_context(data, project, cfg, status_path)
    summary = toolchain_summary(data, project, cfg) if data.get("source") in (None, "startup", "resume", "clear") else None
    if summary:
        hookio.notify("SessionStart", "\n\n".join(parts + [summary]), summary)
    elif parts:
        hookio.add_context("SessionStart", "\n\n".join(parts))


if __name__ == "__main__":
    hookio.run(main, NAME)

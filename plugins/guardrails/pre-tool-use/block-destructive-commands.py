#!/usr/bin/env python3
"""block-destructive-commands: deny catastrophic shell commands; ask before risky, recoverable ones.

PreToolUse on Bash. Commands are parsed into simple commands (operators, substitutions, `sh -c`,
wrappers) and each is evaluated by rule, never by substring, so `echo "rm -rf /"` is harmless text while
`sudo rm -rf /` is denied. Relative recursive deletes inside the project (`rm -rf build`) are allowed.
Config: `disabled: ["block-destructive-commands"]`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, shellparse  # noqa: E402

NAME = "block-destructive-commands"
DENY, ASK = "deny", "ask"
SQL_DESTRUCTIVE = re.compile(r"(?i)\b(drop\s+(database|schema|table)|truncate(\s+table)?\s+\w|delete\s+from\s+[\w.`\"]+\s*(;|$|['\"]))")
AWS_DELETE = re.compile(r"^(delete-db-instance|delete-db-cluster|delete-table|delete-bucket|terminate-instances|delete-stack)$")
DANGEROUS_RM_TARGETS = {"/", "/*", "~", "~/", "*", ".", "..", "./", "../", "$HOME", "${HOME}"}


def flags_of(toks):
    return [t for t in toks[1:] if t.startswith("-")]


def has_short(flags, letters):
    return any(f.startswith("-") and not f.startswith("--") and any(ch in f[1:] for ch in letters) for f in flags)


def outside_project(target, cwd, project):
    if target.startswith(("~", "$HOME", "${HOME}")):
        return True
    path = target if os.path.isabs(target) else os.path.join(cwd, target)
    return config.relative(path, project) in (None, "")


def check_rm(toks, cwd, project):
    flags = flags_of(toks)
    recursive = has_short(flags, "rR") or "--recursive" in flags
    targets = [t for t in toks[1:] if not t.startswith("-") and t != "__SUBST__"]
    if recursive:
        for t in targets:
            if t in DANGEROUS_RM_TARGETS or outside_project(t, cwd, project):
                return DENY, f"recursive delete of '{t}' reaches outside the project or its root"
    return None


def git_subcommand(toks):
    i = 1
    while i < len(toks):
        t = toks[i]
        if t in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
            continue
        if t.startswith("-"):
            i += 1
            continue
        return t, toks[i + 1:]
    return None, []


def check_git(toks):
    sub, rest = git_subcommand(toks)
    flags = [t for t in rest if t.startswith("-")]
    if sub == "push":
        if {"--help", "-h", "--dry-run", "-n"} & set(flags):
            return None
        force = {"-f", "--force", "--force-with-lease", "--force-if-includes", "--mirror", "--delete", "-d"}
        if force & set(flags) or any(f.startswith("--force-with-lease=") for f in flags) or \
                any(t.startswith(("+", ":")) for t in rest if not t.startswith("-")):
            return DENY, "force-push, mirror or remote branch deletion rewrites or destroys shared history"
        return ASK, "git push publishes commits to a remote; it needs explicit authorization"
    if sub in ("filter-branch", "filter-repo"):
        return DENY, "history rewriting tools change every affected commit"
    if sub == "reset" and "--hard" in flags:
        return ASK, "git reset --hard discards uncommitted work"
    if sub == "clean" and (has_short(flags, "f") or "--force" in flags):
        return ASK, "git clean -f deletes untracked files permanently"
    if sub == "checkout" and ("--" in rest or "." in rest or has_short(flags, "f") or "--force" in flags):
        return ASK, "this checkout overwrites uncommitted changes in the working tree"
    if sub == "restore" and ("--staged" not in flags or "--worktree" in flags or "-W" in flags):
        return ASK, "git restore discards uncommitted changes in the working tree"
    if sub == "branch" and ("-D" in flags or ("--delete" in flags and "--force" in flags)):
        return ASK, "force-deleting a branch can lose unmerged commits"
    if sub == "stash" and rest[:1] and rest[0] in ("drop", "clear"):
        return ASK, "dropping stashes loses their changes"
    if sub == "rebase":
        return ASK, "rebase rewrites history"
    if sub == "commit" and "--amend" in flags:
        return ASK, "--amend rewrites the previous commit"
    if sub in ("reflog", "gc") and any(t in ("expire", "--prune=now") for t in rest):
        return ASK, "pruning the reflog removes the safety net for lost commits"
    return None


def check_other(toks, segment_text, cwd, project):
    cmd = toks[0]
    if cmd in ("mysql", "mariadb", "psql", "sqlite3", "mysqlsh") and SQL_DESTRUCTIVE.search(segment_text):
        return DENY, "destructive SQL (DROP, TRUNCATE, or DELETE without WHERE) run directly against a database"
    if cmd in ("python", "python3") and "manage.py" in toks:
        i = toks.index("manage.py")
        sub = toks[i + 1] if i + 1 < len(toks) else ""
        if sub in ("flush", "reset_db"):
            return DENY, f"manage.py {sub} deletes all data"
        if sub == "migrate" and "zero" in toks:
            return ASK, "migrating to zero unapplies every migration of the app"
    if cmd == "terraform":
        if "destroy" in toks or ("apply" in toks and any(t.startswith("-auto-approve") for t in toks)):
            return DENY, "terraform destroy / unattended apply changes infrastructure without review"
        if "apply" in toks:
            return ASK, "terraform apply changes real infrastructure"
    if cmd == "kubectl" and "delete" in toks:
        return ASK, "kubectl delete removes cluster resources"
    if cmd == "aws" and len(toks) > 2:
        if toks[1] == "s3" and (toks[2] == "rb" or (toks[2] == "rm" and "--recursive" in toks)):
            return DENY, "recursive S3 deletion or bucket removal"
        if any(AWS_DELETE.match(t) for t in toks[2:3]):
            return DENY, f"aws {toks[1]} {toks[2]} deletes a resource"
    if cmd.startswith("mkfs") or (cmd == "dd" and any(t.startswith("of=/dev/") for t in toks)):
        return DENY, "writes directly to a device or filesystem"
    if cmd in ("shutdown", "reboot", "halt", "poweroff"):
        return DENY, "stops the machine"
    if cmd in ("chmod", "chown") and (has_short(flags_of(toks), "R") or "--recursive" in toks):
        targets = [t for t in toks[1:] if not t.startswith("-")][1:]
        if any(t in DANGEROUS_RM_TARGETS or outside_project(t, cwd, project) for t in targets):
            return DENY, f"recursive {cmd} outside the project"
    return None


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    if data.get("tool_name") != "Bash" or not config.enabled(cfg, NAME):
        return
    command = hookio.tool_input(data).get("command", "")
    cwd = data.get("cwd") or project
    verdict = None
    for toks in shellparse.simple_commands(command):
        segment = " ".join(toks)
        if toks[0] == "rm":
            found = check_rm(toks, cwd, project)
        elif toks[0] == "git":
            found = check_git(toks)
        else:
            found = check_other(toks, segment, cwd, project)
        if found and (verdict is None or found[0] == DENY):
            verdict = found
        if verdict and verdict[0] == DENY:
            break
    if not verdict:
        return
    kind, why = verdict
    if kind == DENY:
        hookio.deny(f"Blocked by {NAME}: {why}. This is irreversible or affects shared state. If it is truly "
                    "intended, the user must run it themselves.")
    hookio.ask(f"{NAME}: {why}. Confirm that this is intended and authorized.")


if __name__ == "__main__":
    hookio.run(main, NAME)

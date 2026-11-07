"""Read-only git queries for hooks. Every function returns None when git is unavailable or not a repo."""
import subprocess


def _git(project, *args, timeout=10):
    try:
        proc = subprocess.run(["git", "-C", project] + list(args), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout if proc.returncode == 0 else None


def is_repo(project):
    return (_git(project, "rev-parse", "--is-inside-work-tree") or "").strip() == "true"


def status_lines(project):
    out = _git(project, "status", "--porcelain")
    return None if out is None else [l for l in out.splitlines() if l.strip()]


def branch(project):
    out = _git(project, "rev-parse", "--abbrev-ref", "HEAD")
    return out.strip() if out else None


def last_commit(project):
    out = _git(project, "log", "--oneline", "-1")
    return out.strip() if out else None


def is_tracked_in_head(project, path):
    return _git(project, "cat-file", "-e", "HEAD:" + path) is not None


def staged_files(project):
    out = _git(project, "diff", "--cached", "--name-only")
    return None if out is None else [l for l in out.splitlines() if l.strip()]


def modified_tracked_files(project):
    out = _git(project, "diff", "--name-only")
    return None if out is None else [l for l in out.splitlines() if l.strip()]

"""Per-project guardrail configuration: <project>/.claude/guardrails.json (all keys optional)."""
import json
import os
import re

CONFIG_REL = os.path.join(".claude", "guardrails.json")
_cache = {}


def load(project_dir):
    path = os.path.join(project_dir, CONFIG_REL)
    if path in _cache:
        return _cache[path]
    cfg = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            cfg = loaded
    _cache[path] = cfg
    return cfg


def enabled(cfg, hook_name):
    return hook_name not in (cfg.get("disabled") or [])


def patterns(cfg, key, default=()):
    value = cfg.get(key)
    if value is None:
        return list(default)
    return [p for p in value if isinstance(p, str)]


def glob_to_regex(pattern):
    """Glob with `**` (any depth), `*` (within a segment), `?`. Patterns match project-relative paths."""
    i, out = 0, []
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?"); i += 3
        elif pattern.startswith("**", i):
            out.append(".*"); i += 2
        elif c == "*":
            out.append("[^/]*"); i += 1
        elif c == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(c)); i += 1
    return re.compile("^" + "".join(out) + "$")


def relative(path, project_dir):
    path = os.path.normpath(os.path.join(project_dir, path)) if not os.path.isabs(path) else os.path.normpath(path)
    root = os.path.normpath(project_dir)
    if path == root:
        return ""
    if path.startswith(root + os.sep):
        return path[len(root) + 1:].replace(os.sep, "/")
    return None  # outside the project


def matches(path, globs, project_dir):
    """True if `path` matches any glob, tested against the project-relative path and the basename."""
    rel = relative(path, project_dir)
    candidates = [c for c in (rel, os.path.basename(path)) if c]
    for g in globs:
        rx = glob_to_regex(g)
        if any(rx.match(c) for c in candidates):
            return True
    return False

"""Auto-detect a project's formatter and linter for an edited file. Read-only; stdlib only.

A tool is used only when the project both configures it and has it installed locally: nearest config file
walking up from the edited file to the project root, plus the executable in a project virtualenv or
node_modules/.bin (gofmt: on PATH). An executable tracked by git is never run. Commands are fixed argv
lists (no shell) on the edited file alone; whole-project tools (type checkers, golangci-lint) are not
detected.

detect(path, project, kind) returns None for a path outside the project, else a Result: `argv`, `cwd` and
`label` when a tool was found, or `skip` (why not) and `key` (identifies the reason for notices).
"""
import os
import re
import shutil

from lib import gitinfo

FAMILIES = {".py": "python", ".pyi": "python", ".go": "go"}
FAMILIES.update({ext: "js" for ext in (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")})
LABELS = {"python": "Python", "js": "JavaScript/TypeScript", "go": "Go"}
MARKERS = {"python": ("pyproject.toml", "ruff.toml", ".ruff.toml"), "js": ("package.json", "biome.json", "biome.jsonc"),
           "go": ("go.mod",)}

RUFF_FILES = ("ruff.toml", ".ruff.toml")
RUFF_SECTION = re.compile(r"^\s*\[tool\.ruff[\].]", re.M)
VENV_BINS = (".venv/bin", "venv/bin")
JS_CONFIGS = {
    "biome": ("biome.json", "biome.jsonc"),
    "eslint": ("eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts", "eslint.config.mts",
               "eslint.config.cts", ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yml",
               ".eslintrc.yaml"),
    "prettier": (".prettierrc", ".prettierrc.json", ".prettierrc.yml", ".prettierrc.yaml", ".prettierrc.json5",
                 ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.mjs", ".prettierrc.toml", "prettier.config.js",
                 "prettier.config.cjs", "prettier.config.mjs", "prettier.config.ts"),
}
PACKAGE_KEYS = {"eslint": '"eslintConfig"', "prettier": '"prettier"'}
JS_ARGS = {("biome", "format"): ["format", "--write"], ("biome", "lint"): ["lint"],
           ("prettier", "format"): ["--write"], ("eslint", "lint"): []}


class Result(dict):
    @property
    def found(self):
        return "argv" in self


def family(path):
    return FAMILIES.get(os.path.splitext(path)[1].lower())


def _entries(directory):
    try:
        return set(os.listdir(directory))
    except OSError:
        return set()


def _ancestors(start, project):
    """start, its parents, ..., project (inclusive). Empty when start is outside the project."""
    root, here = os.path.realpath(project), os.path.realpath(start)
    if here != root and not here.startswith(root + os.sep):
        return []
    dirs = [here]
    while here != root:
        here = os.path.dirname(here)
        dirs.append(here)
    return dirs


def _rel(path, base):
    return os.path.relpath(path, base).replace(os.sep, "/")


def _executable(dirs, subdirs, name, project):
    """Nearest installed, untracked executable `<dir>/<subdir>/<name>`: (path, None), or (None, reason)."""
    for d in dirs:
        for sub in subdirs:
            candidate = os.path.join(d, sub, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                real = os.path.realpath(candidate)
                for p in {candidate, real}:
                    rel = _rel(p, os.path.realpath(project))
                    if not rel.startswith("..") and gitinfo.is_tracked(project, rel):
                        return None, "tracked"
                return candidate, None
    return None, "missing"


def _ruff_config_dir(dirs):
    for d in dirs:
        names = _entries(d)
        if names.intersection(RUFF_FILES):
            return d
        if "pyproject.toml" in names:
            try:
                with open(os.path.join(d, "pyproject.toml"), encoding="utf-8", errors="replace") as fh:
                    if RUFF_SECTION.search(fh.read()):
                        return d
            except OSError:
                pass
    return None


def _js_config_dir(dirs, tool):
    for d in dirs:
        names = _entries(d)
        if names.intersection(JS_CONFIGS[tool]):
            return d
        key = PACKAGE_KEYS.get(tool)
        if key and "package.json" in names:
            try:
                with open(os.path.join(d, "package.json"), encoding="utf-8", errors="replace") as fh:
                    if key in fh.read():
                        return d
            except OSError:
                pass
    return None


def _where(d, project):
    rel = _rel(d, os.path.realpath(project))
    return "the project root" if rel == "." else rel


def _python(path, dirs, project, kind):
    config_dir = _ruff_config_dir(dirs)
    if not config_dir:
        return Result(skip="no Python %s is configured (looked for ruff in pyproject.toml or ruff.toml)" % _noun(kind),
                      key="python:%s:no-config" % kind)
    exe, why = _executable(dirs, VENV_BINS, "ruff", project)
    if not exe:
        if why == "tracked":
            return Result(skip="ruff in %s is tracked by git, so it is not run" % _where(config_dir, project),
                          key="python:tracked")
        return Result(skip="ruff is configured in %s but not installed in a project virtualenv (.venv/bin/ruff); "
                           "install it there, e.g. `uv add --dev ruff`" % _where(config_dir, project),
                      key="python:no-binary:%s" % config_dir)
    args = ["format"] if kind == "format" else ["check"]
    return Result(argv=[exe] + args + [_rel(path, config_dir)], cwd=config_dir, label="ruff " + args[0])


def _js(path, dirs, project, kind):
    tools = [t for t in ("biome", "prettier", "eslint") if (t, kind) in JS_ARGS]
    configured = {t: d for t, d in ((t, _js_config_dir(dirs, t)) for t in tools) if d}
    if not configured:
        names = " or ".join(tools)
        return Result(skip="no JavaScript/TypeScript %s is configured (looked for %s config)" % (_noun(kind), names),
                      key="js:%s:no-config" % kind)
    if len(configured) > 1:
        return Result(skip="both %s are configured for %s, so neither is run automatically; set commands.%s"
                           % (" and ".join(sorted(configured)), _noun(kind), kind),
                      key="js:%s:conflict" % kind)
    tool, config_dir = next(iter(configured.items()))
    exe, why = _executable(dirs, ("node_modules/.bin",), tool, project)
    if not exe:
        if why == "tracked":
            return Result(skip="%s in node_modules is tracked by git, so it is not run" % tool, key="js:tracked")
        return Result(skip="%s is configured in %s but not installed (node_modules/.bin/%s); run your package "
                           "manager's install" % (tool, _where(config_dir, project), tool),
                      key="js:%s:no-binary:%s" % (tool, config_dir))
    return Result(argv=[exe] + JS_ARGS[(tool, kind)] + [_rel(path, config_dir)], cwd=config_dir,
                  label="biome " + kind if tool == "biome" else tool)


def _go(path, dirs, project, kind):
    module_dir = next((d for d in dirs if "go.mod" in _entries(d)), None)
    if kind == "lint":
        return Result(skip="no Go linter is auto-detected (golangci-lint checks whole packages); set commands.lint",
                      key="go:lint")
    if not module_dir:
        return Result(skip="no go.mod found, so gofmt is not run", key="go:no-module")
    exe = shutil.which("gofmt")
    if not exe:
        return Result(skip="gofmt is not on PATH; install Go", key="go:no-binary")
    return Result(argv=[exe, "-w", _rel(path, module_dir)], cwd=module_dir, label="gofmt")


def _noun(kind):
    return "formatter" if kind == "format" else "linter"


DETECTORS = {"python": _python, "js": _js, "go": _go}


def detect(path, project, kind):
    path = os.path.realpath(os.path.abspath(path))  # same form as the ancestor dirs (macOS: /var -> /private/var)
    dirs = _ancestors(os.path.dirname(path), project)
    if not dirs:
        return None
    fam = family(path)
    if not fam:
        ext = os.path.splitext(path)[1].lower()
        return Result(skip="no formatter or linter is auto-detected for %s" % (ext + " files" if ext else
                            "files like %s" % os.path.basename(path)), key="type:%s" % (ext or os.path.basename(path)))
    return DETECTORS[fam](path, dirs, project, kind)


def project_roots(project, max_depth=3, limit=12):
    """Directories (project-relative) holding a toolchain marker, for the session summary: [(dir, family)]."""
    skip = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "vendor", ".tox", ".next", "target"}
    found, root = [], os.path.realpath(project)
    for here, subdirs, files in os.walk(root):
        depth = 0 if here == root else _rel(here, root).count("/") + 1
        subdirs[:] = sorted(d for d in subdirs if d not in skip and not d.startswith(".")) if depth < max_depth else []
        names = set(files)
        for fam in ("python", "js", "go"):
            if names.intersection(MARKERS[fam]):
                found.append((here, fam))
        if len(found) >= limit:
            break
    return found[:limit]

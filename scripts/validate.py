#!/usr/bin/env python3
"""validate.py: lint the marketplace, its plugins, and every skill. Read-only.

Checks
  marketplace  .claude-plugin/marketplace.json parses; every entry's source exists and holds a
               .claude-plugin/plugin.json with the same name; every plugins/* directory is listed;
               plugin dependencies name plugins in this marketplace.
  skills       plugins/<plugin>/skills/<name>/SKILL.md: frontmatter on line 1, kebab-case `name`
               equal to the directory and unique repo-wide, `description` present and <= 1024 chars
               (WARN above 500: descriptions are always in context).
  wiring       README.md links every skill; each plugin README links its own skills.
  links        relative Markdown links in SKILL.md and skill references/*.md resolve and stay
               inside the skill's directory (other skills are referenced by name).
  sync         bundled copies stay byte-identical to their source.

Usage: python3 scripts/validate.py [-q]     (-q prints only WARN/FAIL lines and the summary)
Exit:  0 = no FAIL, 1 = at least one FAIL.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUIET = "-q" in sys.argv[1:]
DESC_MAX = 1024
DESC_WARN = 500
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")

# (source, copy) pairs that must stay identical.
SYNCED_COPIES = [
    ("plugins/engineering/skills/factory-router/SKILL.md",
     "plugins/engineering/skills/factory-init/assets/factory-router.SKILL.md"),
]

counts = {"OK": 0, "WARN": 0, "FAIL": 0}


def report(level, msg):
    counts[level] += 1
    if level != "OK" or not QUIET:
        print(f"{level:<5} {msg}")


def rel(p):
    return str(Path(p).relative_to(ROOT))


def parse_frontmatter(path):
    """Return (dict, error). Supports `key: value` and `key:` followed by `  - item` lists."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "frontmatter must start on line 1 with ---"
    data, key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            return data, None
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                return None, f"block scalar for '{key}' is not supported; keep it on one line"
            data[key] = [] if value == "" else value.strip("'\"")
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if m and key is not None and isinstance(data.get(key), list):
            data[key].append(m.group(1).strip().strip("'\""))
            continue
        return None, f"unsupported frontmatter line: {line!r}"
    return None, "frontmatter not closed"


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def check_marketplace():
    mp_path = ROOT / ".claude-plugin" / "marketplace.json"
    mp, err = load_json(mp_path)
    if err:
        report("FAIL", f"{rel(mp_path)}: {err}")
        return {}
    plugins, names = {}, set()
    for entry in mp.get("plugins", []):
        name, source = entry.get("name"), entry.get("source", "")
        if not name or not isinstance(source, str) or not source.startswith("./"):
            report("FAIL", f"marketplace entry needs a name and a ./ source: {entry}")
            continue
        if name in names:
            report("FAIL", f"marketplace lists '{name}' twice")
        names.add(name)
        pdir = (ROOT / source).resolve()
        manifest, err = load_json(pdir / ".claude-plugin" / "plugin.json")
        if err:
            report("FAIL", f"{name}: missing or invalid {source}/.claude-plugin/plugin.json ({err})")
            continue
        if manifest.get("name") != name:
            report("FAIL", f"{name}: plugin.json name is '{manifest.get('name')}'")
        for field in ("version", "description"):
            if not manifest.get(field):
                report("FAIL", f"{name}: plugin.json has no {field}")
        plugins[name] = (pdir, manifest)
        report("OK", f"plugin {name} -> {source}")
    listed = {p for p, _ in plugins.values()}
    for d in sorted((ROOT / "plugins").iterdir()):
        if d.is_dir() and d.resolve() not in listed:
            report("FAIL", f"{rel(d)} is not listed in marketplace.json")
    for name, (_, manifest) in plugins.items():
        for dep in manifest.get("dependencies", []):
            dep_name = dep if isinstance(dep, str) else dep.get("name")
            if dep_name not in plugins:
                report("FAIL", f"{name}: dependency '{dep_name}' is not in this marketplace")
    return plugins


CODE_FENCE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
CODE_SPAN = re.compile(r"`[^`\n]*`")


def check_links(md_file, boundary=None):
    """Relative Markdown links must resolve, and stay inside `boundary` (a skill's directory)
    when given: skills reference other skills by name, never by path. Code is not a link."""
    text = CODE_SPAN.sub("", CODE_FENCE.sub("", md_file.read_text(encoding="utf-8")))
    for target in MD_LINK.findall(text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#") or "{" in target or "<" in target:
            continue
        path = target.split("#", 1)[0]
        if not path:
            continue
        resolved = (md_file.parent / path).resolve()
        if not resolved.exists():
            report("FAIL", f"{rel(md_file)}: broken link -> {target}")
        elif boundary is not None and boundary.resolve() not in (resolved, *resolved.parents):
            report("FAIL", f"{rel(md_file)}: link leaves the skill directory -> {target} (reference the skill by name)")


def check_skills(plugins):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    seen = {}
    for name, (pdir, _) in sorted(plugins.items()):
        sdir = pdir / "skills"
        plugin_readme = pdir / "README.md"
        preadme = plugin_readme.read_text(encoding="utf-8") if plugin_readme.exists() else ""
        if not plugin_readme.exists():
            report("FAIL", f"{name}: missing README.md")
        if not sdir.is_dir():
            continue
        for skill_md in sorted(sdir.glob("*/SKILL.md")):
            sk = skill_md.parent.name
            fm, err = parse_frontmatter(skill_md)
            if err:
                report("FAIL", f"{rel(skill_md)}: {err}")
                continue
            ok = True
            sname, desc = fm.get("name", ""), fm.get("description", "")
            if not sname:
                report("FAIL", f"{rel(skill_md)}: missing name"); ok = False
            elif not KEBAB.match(sname) or sname != sk:
                report("FAIL", f"{rel(skill_md)}: name '{sname}' must be kebab-case and equal '{sk}'"); ok = False
            elif sname in seen:
                report("FAIL", f"{rel(skill_md)}: duplicate skill name (also in {seen[sname]})"); ok = False
            seen[sname] = name
            if not desc:
                report("FAIL", f"{rel(skill_md)}: missing description"); ok = False
            elif len(desc) > DESC_MAX:
                report("FAIL", f"{rel(skill_md)}: description is {len(desc)} chars (max {DESC_MAX})"); ok = False
            elif len(desc) > DESC_WARN:
                report("WARN", f"{rel(skill_md)}: description is {len(desc)} chars (target <= {DESC_WARN})")
            if f"({rel(skill_md)})" not in readme:
                report("FAIL", f"README.md does not link {rel(skill_md)}"); ok = False
            if f"(skills/{sk}/SKILL.md)" not in preadme:
                report("FAIL", f"{rel(plugin_readme)} does not link skills/{sk}/SKILL.md"); ok = False
            check_links(skill_md, skill_md.parent)
            for ref in sorted((skill_md.parent / "references").glob("*.md")):
                check_links(ref, skill_md.parent)
            if ok:
                report("OK", rel(skill_md))


def check_sync():
    for src, copy in SYNCED_COPIES:
        a, b = ROOT / src, ROOT / copy
        if a.exists() and b.exists() and a.read_bytes() == b.read_bytes():
            report("OK", f"in sync: {copy}")
        else:
            report("FAIL", f"drift: {copy} differs from {src} (copy the source over)")


def main():
    plugins = check_marketplace()
    check_skills(plugins)
    check_sync()
    print(f"summary: {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['OK']} OK")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

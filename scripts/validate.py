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
  agents       plugins/<plugin>/agents/<name>.md: frontmatter name equals the filename and is unique,
               description present, required sections present, read-only agents (disallowedTools
               containing Write and Edit) don't list Write/Edit in tools, every `plugin:name`
               reference resolves to a skill or agent in that plugin, and the agent is linked from README.md and its plugin README.
  hooks        a plugin's hooks file (manifest "hooks") parses; every registered script exists under the
               plugin; every hook script is registered; each has tests/test_<name>.py and a README entry.
  evals        plugins/<plugin>/evals/**/prompt.md (native `claude plugin eval` format): frontmatter keys
               are allowed ones, each case has graders/*.md with a known type and that type's options,
               and `tool_used` Skill graders name a skill that exists in the plugin.
  counts       the skill, agent and hook counts shown in the README banner and "What's inside" table
               match the repository.
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


AGENT_SECTIONS = ["Mission", "Scope of authority", "Responsibilities", "Not responsible for", "Skills to load",
                  "Inputs", "Output", "Quality criteria", "Escalation", "Human approval required"]
SKILL_REF = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*):([a-z0-9]+(?:-[a-z0-9]+)*)`")


def split_tools(value):
    if isinstance(value, list):
        return {v.strip() for v in value if v.strip()}
    return {v.strip() for v in str(value or "").split(",") if v.strip()}


def check_agents(plugins):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    skills = {(name, d.name) for name, (pdir, _) in plugins.items() for d in (pdir / "skills").glob("*") if (d / "SKILL.md").exists()}
    agents = {(name, a.stem) for name, (pdir, _) in plugins.items() for a in (pdir / "agents").glob("*.md")}
    components = skills | agents
    seen = {}
    for name, (pdir, _) in sorted(plugins.items()):
        preadme_path = pdir / "README.md"
        preadme = preadme_path.read_text(encoding="utf-8") if preadme_path.exists() else ""
        for agent in sorted((pdir / "agents").glob("*.md")):
            fm, err = parse_frontmatter(agent)
            if err:
                report("FAIL", f"{rel(agent)}: {err}")
                continue
            ok = True
            aname = fm.get("name", "")
            if aname != agent.stem or not KEBAB.match(aname):
                report("FAIL", f"{rel(agent)}: name '{aname}' must be kebab-case and equal '{agent.stem}'"); ok = False
            elif aname in seen:
                report("FAIL", f"{rel(agent)}: duplicate agent name (also in {seen[aname]})"); ok = False
            seen[aname] = name
            desc = fm.get("description", "")
            if not desc or len(desc) > DESC_MAX:
                report("FAIL", f"{rel(agent)}: description missing or longer than {DESC_MAX} chars"); ok = False
            tools, denied = split_tools(fm.get("tools")), split_tools(fm.get("disallowedTools"))
            if {"Write", "Edit"} <= denied and tools & {"Write", "Edit", "NotebookEdit"}:
                report("FAIL", f"{rel(agent)}: read-only agent lists Write/Edit in tools"); ok = False
            body = agent.read_text(encoding="utf-8")
            for section in AGENT_SECTIONS:
                if not re.search(rf"^## {re.escape(section)}\b", body, re.M):
                    report("FAIL", f"{rel(agent)}: missing section '## {section}'"); ok = False
            for plugin_name, ref in SKILL_REF.findall(body):
                if plugin_name not in plugins:
                    if "-" in plugin_name and "-" in ref:  # shaped like plugin:component, e.g. a stale name
                        report("FAIL", f"{rel(agent)}: `{plugin_name}:{ref}` names an unknown plugin"); ok = False
                elif (plugin_name, ref) not in components:
                    report("FAIL", f"{rel(agent)}: references unknown skill or agent {plugin_name}:{ref}"); ok = False
            if f"({rel(agent)})" not in readme:
                report("FAIL", f"README.md does not link {rel(agent)}"); ok = False
            if f"(agents/{agent.name})" not in preadme:
                report("FAIL", f"{rel(preadme_path)} does not link agents/{agent.name}"); ok = False
            if ok:
                report("OK", rel(agent))


HOOK_DIRS = ("pre-tool-use", "post-tool-use", "stop", "session")


def check_hooks(plugins):
    for name, (pdir, manifest) in sorted(plugins.items()):
        hooks_rel = manifest.get("hooks")
        if not isinstance(hooks_rel, str):
            continue
        hooks_path = (pdir / hooks_rel).resolve()
        data, err = load_json(hooks_path)
        if err or not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
            report("FAIL", f"{name}: hooks file {hooks_rel} missing or invalid ({err or 'no hooks object'})")
            continue
        registered = set()
        for event, groups in data["hooks"].items():
            for group in groups:
                for h in group.get("hooks", []):
                    for arg in [h.get("command", "")] + list(h.get("args", [])):
                        if "${CLAUDE_PLUGIN_ROOT}/" in arg:
                            rel_script = arg.split("${CLAUDE_PLUGIN_ROOT}/", 1)[1]
                            script = pdir / rel_script
                            if not script.is_file():
                                report("FAIL", f"{name}: {event} hook script not found: {rel_script}")
                            registered.add(script.resolve())
        readme = (pdir / "README.md").read_text(encoding="utf-8") if (pdir / "README.md").exists() else ""
        for d in HOOK_DIRS:
            for script in sorted((pdir / d).glob("*.py")):
                hook = script.stem
                ok = True
                if script.resolve() not in registered:
                    report("FAIL", f"{rel(script)}: not registered in {hooks_rel}"); ok = False
                if not (pdir / "tests" / f"test_{hook.replace('-', '_')}.py").is_file():
                    report("FAIL", f"{rel(script)}: missing tests/test_{hook.replace('-', '_')}.py"); ok = False
                if f"`{hook}`" not in readme:
                    report("FAIL", f"{rel(script)}: not documented in {name} README"); ok = False
                if ok:
                    report("OK", rel(script))


PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
GRADER_KEYS = {"type", "weight", "arm"}
GRADER_TYPES = {"regex": {"pattern", "flags", "match", "target"}, "tool_used": {"tool", "input_match", "min", "max"},
                "tool_order": {"before", "after"}, "file_exists": {"path", "exists"}, "llm": {"criteria", "focus"},
                "baseline": {"baseline_file", "criteria"}}


def check_evals(plugins):
    for name, (pdir, _) in sorted(plugins.items()):
        skills = {d.name for d in (pdir / "skills").glob("*") if (d / "SKILL.md").exists()}
        for prompt in sorted((pdir / "evals").glob("**/prompt.md")):
            if "results" in prompt.relative_to(pdir / "evals").parts:
                continue
            ok = True
            fm, err = parse_frontmatter(prompt)
            if err:
                report("FAIL", f"{rel(prompt)}: {err}"); continue
            unknown = set(fm) - PROMPT_KEYS
            if unknown:
                report("FAIL", f"{rel(prompt)}: unknown prompt.md keys {sorted(unknown)}"); ok = False
            body = prompt.read_text(encoding="utf-8").split("---", 2)[-1].strip()
            if not body:
                report("FAIL", f"{rel(prompt)}: empty prompt body"); ok = False
            graders = sorted((prompt.parent / "graders").glob("*.md"))
            if not graders:
                report("FAIL", f"{rel(prompt)}: case has no graders/*.md"); ok = False
            for g in graders:
                gfm, gerr = parse_frontmatter(g)
                if gerr:
                    report("FAIL", f"{rel(g)}: {gerr}"); ok = False; continue
                gtype = gfm.get("type")
                if gtype not in GRADER_TYPES:
                    report("FAIL", f"{rel(g)}: unknown grader type {gtype!r}"); ok = False; continue
                bad = set(gfm) - GRADER_KEYS - GRADER_TYPES[gtype]
                if bad:
                    report("FAIL", f"{rel(g)}: keys {sorted(bad)} not valid for type {gtype}"); ok = False
                if gtype == "llm" and not g.read_text(encoding="utf-8").split("---", 2)[-1].strip():
                    report("FAIL", f"{rel(g)}: llm grader has no rubric body"); ok = False
                if gtype == "tool_used" and gfm.get("tool") == "Skill":
                    named = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)+", str(gfm.get("input_match", ""))))
                    if not named & skills:
                        report("FAIL", f"{rel(g)}: Skill grader names no skill of {name}"); ok = False
            if ok:
                report("OK", rel(prompt))


BANNER = "docs/assets/agent-skills-banner.svg"


def check_counts(plugins):
    actual = {
        "skills": sum(len(list((pdir / "skills").glob("*/SKILL.md"))) for pdir, _ in plugins.values()),
        "agents": sum(len(list((pdir / "agents").glob("*.md"))) for pdir, _ in plugins.values()),
        "hooks": sum(len(list((pdir / d).glob("*.py"))) for pdir, _ in plugins.values() for d in HOOK_DIRS),
    }
    banner = ROOT / BANNER
    if banner.exists():
        svg = banner.read_text(encoding="utf-8")
        for kind, n in actual.items():
            m = re.search(r">(\d+)</text>\s*<text[^>]*>%s<" % kind, svg)
            if not m:
                report("FAIL", f"{BANNER}: no count found for {kind}")
            elif int(m.group(1)) != n:
                report("FAIL", f"{BANNER}: shows {m.group(1)} {kind}, repository has {n}")
            else:
                report("OK", f"banner {kind} = {n}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for label, kind in (("Skills", "skills"), ("Specialist agents", "agents"), ("Guardrail hooks", "hooks")):
        m = re.search(r"^\| %s \| (\d+)" % re.escape(label), readme, re.M)
        if m and int(m.group(1)) != actual[kind]:
            report("FAIL", f"README.md 'What's inside' shows {m.group(1)} {kind}, repository has {actual[kind]}")


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
    check_agents(plugins)
    check_hooks(plugins)
    check_evals(plugins)
    check_counts(plugins)
    check_sync()
    print(f"summary: {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['OK']} OK")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

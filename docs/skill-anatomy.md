# Skill anatomy

How a skill in this repo is written. Adapted from addyosmani/agent-skills `docs/skill-anatomy.md` and mattpocock/skills conventions, constrained by the Claude Code skill format (https://code.claude.com/docs/en/skills).

A skill explains **how** to do one kind of engineering task. *Who* does it is an agent ([agent-anatomy.md](agent-anatomy.md)); *what is allowed* is a hook ([hook-anatomy.md](hook-anatomy.md)); *the gated multi-stage process* is a Software Factory workflow ([architecture.md](architecture.md#workflows)).

## Location

```
plugins/<profile>/skills/<skill-name>/
  SKILL.md        required; keep under ~300 lines (hard ceiling 500)
  references/     optional: material loaded on demand (checklists, catalogs, long examples)
  scripts/        optional: executables the skill runs via ${CLAUDE_SKILL_DIR}/scripts/...
  assets/         optional: files the skill copies into a target project
```

Move a section into `references/` once it passes ~80 lines or is only needed in some runs. Link every reference file from `SKILL.md` with the condition under which to read it ("Read [references/redaction-catalog.md](references/redaction-catalog.md) when classifying a field").

## Frontmatter

```yaml
---
name: skill-name            # kebab-case, equals the directory name, unique across all plugins
description: Does X for Y. Use when <trigger>, <trigger>, or the user says "<phrase>".
# optional, only when needed:
# disable-model-invocation: true   # user-invoked only (/skill-name); can't be preloaded by agents
# allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/check.sh *)
---
```

- Frontmatter starts on line 1. A leading blank line stops it from being parsed.
- **`description`** is always in context for every session where the plugin is enabled, so it is a budget. Say **what** the skill does (third person), then **when** ("Use when ..."), with phrases a user would type. Target ≤ 400 characters; `validate.py` warns above 500 and fails above 1024. Never summarise the procedure: the model may follow the summary instead of loading the skill.
- One line per value. The validator rejects YAML block scalars.

## Invocation type

| Type | Use for | Frontmatter |
|---|---|---|
| **Model-invoked** (default) | Disciplines Claude should reach for on its own: instrumentation, migrations, review | rich trigger phrases in `description` |
| **User-invoked** | Heavy or side-effecting flows started deliberately (installing the factory) | `disable-model-invocation: true` |

## Required body sections

Every skill answers seven questions. Use these headings (or close equivalents) in this order:

| Heading | Question it answers |
|---|---|
| `## Overview` | What problem does it solve, and why does it matter? (2–4 sentences) |
| `## When to use` | When should Claude activate it? Include **When not to use** with the skill to use instead |
| `## Inputs and context` | What must be read or detected first: project conventions, versions, existing utilities, the factory's `CLAUDE.md` and `tasks/STATUS.md` when present |
| `## Process` | The procedure: numbered steps, decision criteria, approval gates marked ⏸ |
| `## Output` | What it produces and in what shape (file, report section, table) |
| `## Verification` | Exit checklist with the evidence required (commands actually run) |
| `## Escalation` | When to stop and ask a human |

Recommended after those: `## Common rationalizations` (excuse → reality table), `## Red flags`, `## References`.

## Writing rules

- **Actionable, checkable steps.** No vague advice. Every step is something the agent can do and verify.
- **Inspect before prescribing.** Start from the target project's conventions, versions, and existing abstractions. Never invent APIs (loggers, clients, internal frameworks) without reading their implementation.
- **Version-aware.** State which behavior is version-specific ("Python ≥ 3.10", "Django ≥ 4.1"). Never assume a modern feature exists in a legacy project; detect the version first.
- **Decision criteria over rules of thumb.** When a choice exists, give the criteria that decide it and the failure scenario of choosing wrong.
- **Evidence over assertion.** Verification reports actual command output; unknowns are labeled, not guessed.
- **Composable.** Hand off by name ("for correlation propagation, apply `distributed-tracing-and-correlation`"). Don't copy another skill's content.
- **Factory-aware, factory-optional.** When `.factory/` exists, write outputs where the factory expects them (`specs/`, `tasks/`, `product/`) and follow its gates. The skill must still work in a repo without a factory.
- **Project specifics stay out.** Defaults go in `references/`; the target project's own `CLAUDE.md` overrides them.
- **No placeholders.** A skill is committed only when every section is real.

## Checklist before committing a skill

- [ ] `python3 scripts/validate.py` reports 0 FAIL (frontmatter, name, description length, links, README wiring)
- [ ] All seven required sections present and specific to this skill
- [ ] Linked from `README.md` and the plugin `README.md`
- [ ] No overlap with an existing skill or Software Factory document (link instead)
- [ ] Critical skills have eval coverage in `evals/` (see [architecture.md](architecture.md#evaluations))

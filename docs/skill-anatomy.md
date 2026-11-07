# Skill anatomy

How a skill in this repo is written. Adapted from addyosmani/agent-skills `docs/skill-anatomy.md` and mattpocock/skills conventions.

## Location

```
plugins/<profile>/skills/<skill-name>/
  SKILL.md        required
  references/     optional: material loaded on demand (guidelines, templates, checklists)
  scripts/        optional: executables the skill runs by absolute path
  assets/         optional: files the skill copies into a target project
```

Add a supporting folder only when the skill needs it. Move content out of `SKILL.md` into `references/` once a section passes ~100 lines or is only needed in some runs.

## Frontmatter

```yaml
---
name: skill-name            # kebab-case, equals the directory name, unique repo-wide
description: Does X for Y. Use when <trigger>, <trigger>, or the user says "<phrase>".
# optional:
# disable-model-invocation: true   # user-invoked only (reachable via /skill-name)
# allowed-tools: Read, Grep, Bash
---
```

- The frontmatter must start on line 1. A leading blank line stops it from being parsed.
- `description` (max 1024 chars) is what the model sees when deciding to load the skill. Say **what** it does (third person), then **when** ("Use when ..."), with the trigger phrases a user would actually type. Don't summarise the steps: the model may follow the summary instead of reading the skill.

## Invocation type

Choose one per skill (from mattpocock/skills):

| Type | Use for | Frontmatter |
|---|---|---|
| **Model-invoked** | Discipline the model should reach for on its own (routing, reviewing, interviewing on a blog idea) | default; rich trigger phrases in `description` |
| **User-invoked** | Heavy or side-effecting flows you start deliberately (installing a factory, publishing) | `disable-model-invocation: true` |

## Body

Recommended sections (from addyosmani/agent-skills). Equivalent headings are fine.

```markdown
# Skill Title

## Overview          one or two sentences: what and why
## When to use       triggers, and when NOT to use it (point to the right skill instead)
## Process           numbered steps or phases; mark approval gates explicitly (⏸)
## Techniques        patterns, templates, examples
## Common rationalizations   | Excuse to skip a step | Why it's wrong |
## Red flags         signs the skill is being violated
## Verification      exit checklist with the evidence required
```

## Writing rules

- Actionable process, not vague advice. Every step should be something the agent can do and check.
- Hard rules up front (what never to do: invent facts, overwrite files, skip approval).
- Evidence over assertion: verification reports actual command output.
- Hand-offs by name: "when the outline is approved, use `blog-visual-storyteller`". Don't copy another skill's content.
- Keep project specifics out of the skill body. Put defaults in `references/` and tell the skill to prefer the target project's own conventions (its `CLAUDE.md`) when they exist.

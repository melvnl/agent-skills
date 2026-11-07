# Agent anatomy

How a specialist agent (subagent) in this repo is written. Format: Claude Code subagent Markdown files (https://code.claude.com/docs/en/sub-agents).

An agent defines **who** does a piece of work: a role with responsibilities, boundaries, and a deliverable. *How* the work is done lives in skills, which the agent loads by name. Agents never restate skill content.

## Location and naming

```
plugins/<profile>/agents/<agent-name>.md
```

- Put the agent in the plugin whose skills it mainly uses, so installing a profile brings its personas.
- Installed plugin agents are namespaced: `melvin-backend:backend-engineer`. User-level agents (`~/.claude/agents/`) with the same bare name take precedence.
- Agents must be in the plugin's default `agents/` directory. Explicit manifest lists were not picked up in install testing.

## Frontmatter

```yaml
---
name: observability-engineer        # kebab-case, equals the filename, unique across plugins
description: Independently reviews ... Use when ... Read-only.
tools: Read, Grep, Glob, Bash        # allowlist; omit Write/Edit for reviewers
disallowedTools: Write, Edit, NotebookEdit
model: inherit
---
```

- `description` tells the main session **when to delegate**. Name the trigger and the authority ("Read-only").
- Plugin agents **ignore** `hooks`, `mcpServers`, and `permissionMode`, so authority comes from `tools` and `disallowedTools` only.
- **Skills are loaded explicitly, not preloaded.** The body names the skills to invoke with the Skill tool at the start of work (`melvin-observability:structured-logging-and-instrumentation`). Preloading injects whole skills into context, and resolving namespaced plugin names in `skills:` is unverified.

## Authority classes

| Class | Tools | May modify |
|---|---|---|
| **Read-only reviewer** (security, fintech, observability, code review) | `Read, Grep, Glob, Bash` + `disallowedTools: Write, Edit, NotebookEdit` | Nothing. `Bash` is for `git diff/log/show` and running tests. This is **instruction-level** read-only, backed by the guardrail hooks; it is not enforced by the tool list |
| **Document author** (requirements analyst, architect, orchestrator) | `Read, Grep, Glob, Write, Edit, Bash` | Only the documents it owns (`product/`, `specs/`, `engineering/adr/`, `tasks/`) |
| **Implementer** (backend, database engineer) | full set | Source and tests within the approved task scope |

Hard rules for every agent:
1. An implementer never approves its own work. Verification and review come from a different agent or the human.
2. No commits, pushes, merges, deployments, or production operations without explicit human approval.
3. Don't spawn further subagents unless the agent file says so and why (only the orchestrator, for independent parallel reviews).
4. Report only what was observed. Commands not run are reported as not run.

## Required body sections

| Heading | Content |
|---|---|
| `## Mission` | Primary responsibility in 1–2 sentences |
| `## Scope of authority` | What it decides alone, and the file modification permissions |
| `## Responsibilities` | Numbered, checkable duties |
| `## Not responsible for` | Explicit non-responsibilities, each naming who owns it instead |
| `## Skills to load` | Skills by namespaced name, with when to load each |
| `## Inputs` | What the caller must provide (diff range, spec path, task id); what to do when inputs are missing |
| `## Output` | The exact deliverable shape (template) |
| `## Quality criteria` | How a good deliverable is judged |
| `## Escalation` | Conditions that stop the work and go to the human |
| `## Human approval required` | Actions it may propose but never take alone |

## Checklist before committing an agent

- [ ] `python3 scripts/validate.py` reports 0 FAIL
- [ ] Authority class matches the tool list (reviewers have no Write/Edit)
- [ ] Every skill named in *Skills to load* exists in this repo
- [ ] Linked from `README.md` and the plugin `README.md`

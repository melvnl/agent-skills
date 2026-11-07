# Contribution guide

How to add or change a component. The anatomy docs define the formats; this guide is the checklist and the order of work.

## Before adding anything

1. Search for an existing capability: skills (`plugins/*/skills/`), agents, hooks, Software Factory workflows and templates, and the Claude Code built-ins (`/code-review`, `/simplify`, `/security-review`). Prefer extending over adding a near-duplicate. For example, spec-driven development, technical design, ADRs, code review and refactoring are covered by the Software Factory and built-ins rather than separate skills.
2. Pick the right type: *how* → skill; *who* → agent; *deterministic allow/deny/flag* → hook; *ordered, gated process* → factory workflow ([architecture.md](architecture.md)).
3. Pick the plugin by profile: put a component where the projects that need it will have it installed.

## Adding a skill

1. Follow [skill-anatomy.md](skill-anatomy.md): frontmatter on line 1, `name` = directory, description ≤ 400 chars with "Use when", the seven required sections.
2. Put long material in `references/` and link it with when to read it. No links outside the skill's directory; reference other skills by name.
3. Link the skill from the plugin `README.md` and the top-level `README.md`.
4. Critical skills get eval cases in `plugins/<profile>/evals/` (positive, false-positive, and a must-not-trigger case where useful).

## Adding an agent

1. Follow [agent-anatomy.md](agent-anatomy.md): ten required sections; authority class matches the tool list (reviewers: no Write/Edit); skills loaded explicitly by `melvin-x:skill` name.
2. Put it in `plugins/<profile>/agents/` (the default directory; manifest lists aren't picked up).
3. Link it from both READMEs.

## Adding a hook

1. Follow [hook-anatomy.md](hook-anatomy.md): stdlib-only Python 3.8+, `lib/hookio.run`, deny/ask only for high-confidence cases, feedback otherwise, never echo secrets.
2. Write `tests/test_<name>.py` with a true positive, a true negative, a false-positive trap, and malformed input.
3. Register it in `plugins/guardrails/hooks.json` (exec form, narrow matcher, timeout) and add a row to the plugin README's hook table.
4. Run the tests on the oldest Python you support (`/usr/bin/python3` on macOS is often 3.9).

## Changing the Software Factory

- Edit `plugins/engineering/skills/factory-init/assets/factory/`; keep it project-agnostic (skills and agents named only as optional accelerators).
- New workflows: wire them into `factory-router` (both copies), `references/CLAUDE_TEMPLATE.md`, and the factory `README.md` in the same change.
- Run `factory-init/scripts/verify_factory.sh` against a throwaway install to check internal references.

## Checks before committing

```bash
scripts/agent-skills validate          # validator, hook tests, trace_check tests
claude plugin validate plugins/<profile>
```

Evals cost usage: run the cases you touched with `claude plugin eval plugins/<profile> --case <name> --runs 1 --ablation none`, and read traces (`--keep-temp`) before changing a skill because a grader failed. The rubric may be the problem.

## Commits

- One independently meaningful module per commit; shared infrastructure separately from capabilities.
- Conventional Commits (`feat(skills): add ...`, `feat(hooks): ...`, `fix(...)`, `docs: ...`).
- Stage explicit paths; never `git add -A`, `git add .`, or `git commit -a`. Check `git status` before and after.
- Every commit's tree passes the validator on its own: add references after the things they reference exist.
- No amend, squash, rebase, force-push, or push without the owner's approval.

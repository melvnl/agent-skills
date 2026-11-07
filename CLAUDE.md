# melvin-skills

This repo is a Claude Code marketplace of reusable capabilities. This file configures agents working **on this repo**; it is not meant to be copied into other projects.

## Structure

- `.claude-plugin/marketplace.json` lists every plugin. The repo root is a marketplace, not a plugin.
- `plugins/<profile>/` is one self-contained plugin: `.claude-plugin/plugin.json`, `README.md`, `skills/<name>/SKILL.md`, `agents/<name>.md`, `evals/<suite>/<case>/`. Plugins use only Claude Code's **default directories**; explicit component path lists were not picked up in install testing.
- `plugins/guardrails/` holds the hooks: `hooks.json`, `pre-tool-use/`, `post-tool-use/`, `stop/`, `session/`, shared `lib/`, `tests/`.
- The Software Factory bundle lives in `plugins/engineering/skills/factory-init/assets/factory/` (core, workflows, templates).
- `scripts/`: `validate.py`, `agent-skills` (install/update/doctor/validate), `bootstrap.sh`, `profiles.json`.
- `docs/`: architecture, skill/agent/hook anatomy, adoption, contribution, release. `docs/ROADMAP.md` and `docs/IMPLEMENTATION_PLAN.md` are local, git-ignored planning notes.

## Rules

- Follow the anatomy docs (`docs/skill-anatomy.md`, `docs/agent-anatomy.md`, `docs/hook-anatomy.md`) for every new or reworked component, and `docs/contribution-guide.md` for the checklist.
- Every skill and agent is linked from `README.md` and its plugin's `README.md`; every hook is registered in `hooks.json`, tested, and listed in the guardrails README.
- Names equal their directory or file name and are unique across all plugins.
- A plugin can't read files outside its own directory once installed. Skills reference only their own folder, or other skills by name.
- `plugins/engineering/skills/factory-init/assets/factory-router.SKILL.md` is a bundled copy of `plugins/engineering/skills/factory-router/SKILL.md`. Edit the source, then copy it over. The validator fails on drift.
- `.factory/` content stays project-agnostic; new workflows are wired into the router, `CLAUDE_TEMPLATE.md` and the factory README together.
- Hooks: stdlib-only Python 3.8+; deny or ask only for high-confidence cases; never echo secret values; project commands run only behind the `run_project_commands` opt-in.
- Prefer extending an existing component over adding a near-duplicate. Don't restate one skill's content in another; reference it by name.
- Commits: one independently meaningful module per commit, Conventional Commits, explicit `git add <paths>` (never `git add -A` or `.`), each commit's tree valid on its own, no amend, squash, force-push, or push without approval.

## Commands

- All repository checks: `scripts/agent-skills validate` (validator + hook tests + trace_check tests)
- Validator only: `python3 scripts/validate.py` (must end with `0 FAIL`)
- Hook tests: `python3 -m unittest discover -s plugins/guardrails/tests` (also run with `/usr/bin/python3`)
- Plugin manifests: `claude plugin validate .` and `claude plugin validate plugins/<profile>`
- Evals (cost usage, run deliberately): `claude plugin eval plugins/<profile> --case <name> --runs 1 --ablation none`

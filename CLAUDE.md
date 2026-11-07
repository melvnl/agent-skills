# melvin-skills

This repo is a Claude Code marketplace of reusable capabilities. This file configures agents working **on this repo**; it is not meant to be copied into other projects.

## Structure

- `.claude-plugin/marketplace.json` lists every plugin. The repo root is a marketplace, not a plugin.
- `plugins/<profile>/` is one self-contained plugin: `.claude-plugin/plugin.json`, `README.md`, `skills/<name>/SKILL.md`. Plugins use only Claude Code's **default directories** (`skills/`, `agents/`); explicit component path lists were not picked up in install testing.
- Optional per-skill folders: `references/` (loaded on demand), `scripts/` (executables), `assets/` (files a skill installs into a project).
- `docs/skill-anatomy.md` is the writing guide. `docs/ROADMAP.md` and `docs/IMPLEMENTATION_PLAN.md` are local, git-ignored planning notes.

## Rules

- Follow `docs/skill-anatomy.md` for every new or reworked skill.
- Every skill is linked from `README.md` and from its plugin's `README.md`.
- `name` in frontmatter equals the directory name and is unique across all plugins.
- A plugin can't read files outside its own directory once installed. Skills reference only their own folder, or other skills by name.
- `plugins/engineering/skills/factory-init/assets/factory-router.SKILL.md` is a bundled copy of `plugins/engineering/skills/factory-router/SKILL.md`. Edit the source, then copy it over. The validator fails on drift.
- `.factory/` content (under `factory-init/assets/factory/`) stays project-agnostic.
- Prefer extending an existing skill over adding a near-duplicate. Don't restate one skill's content in another; reference it by name.
- Commits: one independently meaningful module per commit, Conventional Commits, explicit `git add <paths>` (never `git add -A` or `.`), no amend, squash, force-push, or push without approval.

## Commands

- Validate: `python3 scripts/validate.py` (must end with `0 FAIL`)
- Plugin manifests: `claude plugin validate .` (marketplace) and `claude plugin validate plugins/<profile>`

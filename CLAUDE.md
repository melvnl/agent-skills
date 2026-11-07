# melvin-skills

This repo is a collection of agent skills. This file configures agents working **on this repo**; it is not meant to be copied into other projects.

## Structure

- `skills/<bucket>/<skill-name>/SKILL.md`: one directory per skill. Buckets: `writing/`, `engineering/`.
- Optional per-skill folders: `references/` (docs loaded on demand), `scripts/` (executables), `assets/` (files the skill copies or installs).
- `.claude-plugin/plugin.json` lists every skill explicitly.
- `docs/skill-anatomy.md` is the writing guide. `docs/ROADMAP.md` is a local, git-ignored plan.

## Rules

- Follow `docs/skill-anatomy.md` for every new or reworked skill.
- Every skill must appear in `.claude-plugin/plugin.json` `skills` and be linked from `README.md` (and its bucket `README.md`).
- `name` in frontmatter must equal the directory name and be unique across buckets (harness skill dirs are flat).
- Skills must be self-contained: no references to files outside their own directory, except other skills by name. Project-specific facts (paths, components, palettes) go in the skill's `references/`, phrased as overridable defaults.
- `skills/engineering/factory-init/assets/factory-router.SKILL.md` is a bundled copy of `skills/engineering/factory-router/SKILL.md`. Edit the source, then copy it over. The validator fails on drift.
- Prefer extending an existing skill over adding a near-duplicate. Don't restate one skill's content in another; reference it by name.
- When adding, renaming, or removing a skill, update the pipeline lines in `README.md` so the map of how skills connect stays accurate.

## Commands

- Validate: `scripts/validate-skills.sh` (must end with `summary: 0 FAIL`)
- Plugin manifest: `claude plugin validate . --strict` after touching `.claude-plugin/`
- Reinstall after changes: bump `version` in `.claude-plugin/plugin.json`, then `claude plugin marketplace update melvin-skills && claude plugin update melvin-skills@melvin-skills`

# melvin-skills

Personal agent skills for Claude Code (and any [Agent Skills](https://agentskills.io)-compatible harness).
Inspired by [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (lifecycle-ordered, process-heavy skills) and [mattpocock/skills](https://github.com/mattpocock/skills) (bucketed, small, composable skills).

## Skills

### Writing: engineering blog pipeline

`blog-interviewer` → `blog-architect` → *(draft)* → `blog-visual-storyteller` → `blog-editor`

- **[blog-interviewer](skills/writing/blog-interviewer/SKILL.md)**: Interviews you, one question at a time, to find the story worth publishing and the evidence behind it.
- **[blog-architect](skills/writing/blog-architect/SKILL.md)**: Turns an interview summary into a thesis, narrative structure, and approved outline.
- **[blog-visual-storyteller](skills/writing/blog-visual-storyteller/SKILL.md)**: Designs SVG diagrams and memes for the article and embeds them with `ImageCaption`.
- **[blog-editor](skills/writing/blog-editor/SKILL.md)**: Reviews a draft for technical accuracy, narrative, style, and publication readiness.

### Engineering: software factory

- **[factory-init](skills/engineering/factory-init/SKILL.md)**: Installs the `.factory/` spec-driven software factory into a repo, populates project docs from evidence, and verifies it.
- **[factory-router](skills/engineering/factory-router/SKILL.md)**: Classifies and sizes every request in a factory repo and routes it to the right workflow and approval gates.

## Install

Install as a Claude Code plugin from this repo's own marketplace:

```bash
claude plugin marketplace add /Users/melvin.fa/Documents/private/personal/agent-skills   # or the GitHub repo once pushed
claude plugin install melvin-skills@melvin-skills
```

After editing a skill, bump `version` in `.claude-plugin/plugin.json`, then pull the change in:

```bash
claude plugin marketplace update melvin-skills
claude plugin update melvin-skills@melvin-skills
```

Only skills listed in `.claude-plugin/plugin.json` are installed.

## Layout

```
skills/
  writing/        content and article workflows
  engineering/    code and repo workflows
scripts/
  validate-skills.sh   lint frontmatter, naming, manifest and README wiring
docs/
  skill-anatomy.md     how a skill is written here
.claude-plugin/        plugin.json + marketplace.json
```

Agent personas (`agents/`) and hooks (`hooks/`) are planned.

## Contributing (to myself)

1. Read [docs/skill-anatomy.md](docs/skill-anatomy.md).
2. Add the skill under a bucket, then list it in `.claude-plugin/plugin.json` and this README.
3. Run `scripts/validate-skills.sh` until it reports `0 FAIL`.

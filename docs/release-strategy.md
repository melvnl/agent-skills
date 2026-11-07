# Release strategy

## Versions

Each plugin has its own `version` in `.claude-plugin/plugin.json`, roughly semver:

| Change | Bump |
|---|---|
| New skill, agent, hook, workflow, or eval; additive guidance | minor |
| Wording, fixes, tests, false-positive fixes | patch |
| Renamed or removed skill or agent; a hook that newly denies or asks for common operations; changed `guardrails.json` keys | major (or minor while `0.x`), with a note in the commit body |

Names are compatibility identifiers: other skills, agents, evals, and the user's habits refer to them. Rename only with a reason.

## How installs pick up changes

| Marketplace source | Behavior |
|---|---|
| Local checkout (`claude plugin marketplace add /path/to/agent-skills`) | Plugins are read from their folders: changes apply at the next session start or `/reload-plugins`. Versions don't gate updates |
| GitHub repository | `version` pins installs: bump it, push (with approval), then `scripts/agent-skills update` on each machine |

## Tags

`claude plugin tag plugins/<profile>` creates a `<name>--v<version>` git tag for a plugin release. Tag after the release commit, from a clean tree, and push tags only with approval.

## Pre-release checks

1. `scripts/agent-skills validate` passes.
2. `claude plugin validate .` and `claude plugin validate plugins/<profile>` pass for each changed plugin.
3. Eval cases for changed skills run once (`--runs 1`), with failures triaged by reading traces.
4. A fresh isolated install works: `CLAUDE_CONFIG_DIR=$(mktemp -d) scripts/agent-skills install --profile <p> && scripts/agent-skills doctor`.
5. The factory bundle verifies against a throwaway install when it changed.

## Changelog

Commit history is the changelog: Conventional Commit subjects per plugin scope, with bodies that explain why. A release commit can summarize the range (`git log --oneline <prev-tag>..HEAD -- plugins/<profile>`).

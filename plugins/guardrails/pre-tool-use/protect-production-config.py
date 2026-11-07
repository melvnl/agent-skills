#!/usr/bin/env python3
"""protect-production-config: ask before editing production configuration or deployment definitions.

PreToolUse on Edit, Write and MultiEdit. Defaults cover common layouts (production settings modules,
prod deploy and Kubernetes directories, production YAML, Terraform under prod paths); `production_config`
globs in .claude/guardrails.json add project-specific ones. `disabled` turns it off.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio  # noqa: E402

NAME = "protect-production-config"
DEFAULT_GLOBS = ["**/settings/prod*.py", "**/settings/production*.py", "**/config/production*.*",
                 "**/deploy/prod*/**", "**/deployment/prod*/**", "**/k8s/prod*/**", "**/helm/**/values-prod*.y*ml",
                 "**/*production*.y*ml", "**/terraform/**/prod*/**", "**/infra/**/prod*/**"]


def main(data):
    project = hookio.project_dir(data)
    cfg = config.load(project)
    path = hookio.tool_input(data).get("file_path", "")
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit") or not path or not config.enabled(cfg, NAME):
        return
    if config.matches(path, DEFAULT_GLOBS + config.patterns(cfg, "production_config"), project):
        rel = config.relative(path, project) or path
        hookio.ask("%s: %s looks like production configuration. Changes here affect live systems on the next "
                   "deploy; confirm it is intended, reviewed, and contains no secrets." % (NAME, rel))


if __name__ == "__main__":
    hookio.run(main, NAME)

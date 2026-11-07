#!/usr/bin/env bash
# detect_stack.sh — read-only inventory of a repository for factory-init.
# Usage: detect_stack.sh [repo_root]   (default: current directory)
# Prints evidence only (file names, versions, scripts). It never writes anything.
# Interpretation is the agent's job: every line here is a signal, not a conclusion.

set -u
ROOT="${1:-.}"
cd "$ROOT" || { echo "error: cannot cd to $ROOT" >&2; exit 2; }

has() { [ -e "$1" ]; }
section() { printf '\n## %s\n' "$1"; }
SKIP_DIRS='-not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.next/*" -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/.venv/*" -not -path "*/vendor/*" -not -path "*/target/*"'
findf() { eval find . -maxdepth "${2:-3}" -name "'$1'" $SKIP_DIRS 2>/dev/null | sort | head -20; }

echo "# Repository inventory: $(pwd)"

section "Version control"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "git: yes; branch=$(git branch --show-current 2>/dev/null)"
  echo "remotes: $(git remote -v 2>/dev/null | awk '{print $1"="$2}' | sort -u | tr '\n' ' ')"
  echo "uncommitted files: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  echo "recent commits:"; git log --oneline -5 2>/dev/null | sed 's/^/  /'
  echo "commit count: $(git rev-list --count HEAD 2>/dev/null || echo 0)"
else
  echo "git: no"
fi

section "Existing agent / factory files"
for f in CLAUDE.md AGENTS.md .cursorrules .github/copilot-instructions.md .factory .claude/skills/factory-router/SKILL.md \
         product engineering specs tasks tasks/STATUS.md docs README.md CONTRIBUTING.md ARCHITECTURE.md; do
  has "$f" && echo "exists: $f"
done
has .factory || echo "missing: .factory (bootstrap needed)"

section "Top-level layout"
ls -1A | grep -vE '^(\.git|node_modules|\.DS_Store)$' | head -60

section "Language / build manifests"
for f in package.json pnpm-lock.yaml yarn.lock package-lock.json bun.lockb bun.lock deno.json \
         pyproject.toml requirements.txt Pipfile poetry.lock uv.lock setup.py \
         go.mod Cargo.toml Gemfile composer.json pom.xml build.gradle build.gradle.kts settings.gradle \
         pubspec.yaml Package.swift mix.exs Makefile justfile Taskfile.yml CMakeLists.txt; do
  has "$f" && echo "found: $f"
done
cs=$(findf '*.csproj' 3); [ -n "$cs" ] && echo "found: $cs"
ws=$(findf 'package.json' 3 | grep -v '^./package.json$'); [ -n "$ws" ] && { echo "nested package.json (monorepo?):"; echo "$ws" | sed 's/^/  /'; }
for f in pnpm-workspace.yaml turbo.json nx.json lerna.json; do has "$f" && echo "monorepo signal: $f"; done

if has package.json; then
  section "package.json"
  if command -v node >/dev/null 2>&1; then
    node -e '
      const p = require(require("path").resolve("package.json"));
      const show = (k) => p[k] && console.log(k + ": " + JSON.stringify(p[k]));
      ["name","version","type","engines","packageManager"].forEach(show);
      for (const k of ["scripts","dependencies","devDependencies"]) {
        if (!p[k]) continue;
        console.log(k + ":");
        for (const [n, v] of Object.entries(p[k])) console.log("  " + n + ": " + v);
      }'
  else
    sed -n '1,200p' package.json
  fi
fi

if has pyproject.toml; then section "pyproject.toml (head)"; sed -n '1,80p' pyproject.toml; fi
if has requirements.txt; then section "requirements.txt"; head -50 requirements.txt; fi
if has go.mod; then section "go.mod"; head -40 go.mod; fi
if has Cargo.toml; then section "Cargo.toml"; head -60 Cargo.toml; fi
if has Gemfile; then section "Gemfile"; grep -E "^\s*(gem|ruby)" Gemfile | head -40; fi
if has composer.json; then section "composer.json"; head -60 composer.json; fi
if has pubspec.yaml; then section "pubspec.yaml"; head -60 pubspec.yaml; fi
if has Makefile; then section "Makefile targets"; grep -E '^[a-zA-Z0-9_.-]+:' Makefile | cut -d: -f1 | sort -u | head -40; fi

section "Tooling and config files"
for pat in 'tsconfig*.json' '.eslintrc*' 'eslint.config.*' '.prettierrc*' 'biome.json*' 'ruff.toml' '.flake8' 'mypy.ini' \
           'vitest.config.*' 'jest.config.*' 'playwright*.config.*' 'cypress.config.*' 'pytest.ini' 'tox.ini' 'conftest.py' \
           'next.config.*' 'vite.config.*' 'nuxt.config.*' 'svelte.config.*' 'astro.config.*' 'angular.json' 'remix.config.*' \
           'tailwind.config.*' 'postcss.config.*' 'Dockerfile*' 'docker-compose*.yml' 'compose*.yaml' \
           '.env.example' '.nvmrc' '.node-version' '.python-version' '.tool-versions' 'schema.prisma' 'drizzle.config.*' 'alembic.ini'; do
  r=$(findf "$pat" 2); [ -n "$r" ] && echo "$r"
done
for d in supabase prisma migrations db .github/workflows .gitlab-ci.yml .circleci infra terraform k8s helm; do
  has "$d" && echo "dir/file: $d"
done
if has .github/workflows; then echo "CI workflows:"; ls -1 .github/workflows | sed 's/^/  /'; fi

section "Source and test footprint (file counts by extension, excluding vendored dirs)"
eval find . -type f $SKIP_DIRS -not -path '"./.claude/*"' -not -path '"./.factory/*"' 2>/dev/null \
  | sed -n 's/.*\.\([A-Za-z0-9]*\)$/\1/p' | sort | uniq -c | sort -rn | head -15
echo "test-like files: $(eval find . -type f $SKIP_DIRS 2>/dev/null | grep -cE '(\.|_)(test|spec)\.|/tests?/|/__tests__/')"

section "Docs present"
eval find . -maxdepth 3 -name "'*.md'" $SKIP_DIRS -not -path '"./.claude/*"' -not -path '"./.factory/*"' 2>/dev/null | sort | head -40

echo
echo "# end of inventory"

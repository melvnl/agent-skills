#!/usr/bin/env bash
# bootstrap.sh: set up this capability repository on a new machine.
#
#   bootstrap.sh [--repo <git-url>] [--dir DIR] [--profile P]... [--scope user|project|local]
#   (default --repo: https://github.com/melvnl/agent-skills)
#
# 1. Checks prerequisites (git, claude, python3 >= 3.8).
# 2. Clones the repository into DIR (default: ~/dev/agent-skills), or fast-forwards an existing checkout of
#    the same remote. A non-git directory or a checkout of another remote is never touched.
# 3. Runs `agent-skills install` with the given profiles (default: core), then `agent-skills doctor`.
#
# It writes nothing but the checkout; Claude Code settings change only through `claude plugin` commands.
# No credentials are read or stored: private repositories use your existing git credentials.
set -euo pipefail

repo="https://github.com/melvnl/agent-skills" dir="${HOME}/dev/agent-skills" scope="user"; profiles=()
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo="${2:?}"; shift 2 ;;
    --dir) dir="${2:?}"; shift 2 ;;
    --profile) profiles+=(--profile "${2:?}"); shift 2 ;;
    --scope) scope="${2:?}"; shift 2 ;;
    -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "bootstrap: unknown option $1" >&2; exit 2 ;;
  esac
done

for tool in git claude python3; do
  command -v "$tool" >/dev/null 2>&1 || { echo "bootstrap: '$tool' not found on PATH" >&2; exit 1; }
done
python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' || { echo "bootstrap: python3 >= 3.8 required" >&2; exit 1; }

if [ -d "$dir/.git" ]; then
  current="$(git -C "$dir" remote get-url origin 2>/dev/null || true)"
  if [ "$current" != "$repo" ]; then
    echo "bootstrap: $dir is a checkout of '$current', not '$repo'; leaving it untouched" >&2; exit 1
  fi
  echo "updating existing checkout in $dir"
  git -C "$dir" pull --ff-only
elif [ -e "$dir" ]; then
  echo "bootstrap: $dir exists and is not a git checkout; choose another --dir" >&2; exit 1
else
  mkdir -p "$(dirname "$dir")"
  git clone "$repo" "$dir"
fi

"$dir/scripts/agent-skills" install "${profiles[@]}" --scope "$scope"
"$dir/scripts/agent-skills" doctor

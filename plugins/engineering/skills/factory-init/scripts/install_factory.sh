#!/usr/bin/env bash
# install_factory.sh — copy the bundled, project-agnostic factory into a repository.
# Usage: install_factory.sh [--dry-run] [--with-router] [repo_root]
#
# Never overwrites: every existing target is reported as SKIP and left untouched.
# Prints one line per file: CREATE <path> | SKIP <path> (exists, identical) | CONFLICT <path> (exists, differs)
# | LEGACY <path> (the file exists under its pre-rename UPPER_SNAKE name; left untouched, rename command printed).
# Exit codes: 0 = done (or dry run clean), 3 = conflicts found (nothing for those files was written).

set -eu
DRY=0; ROUTER=0; ROOT="."
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --with-router) ROUTER=1 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) ROOT="$a" ;;
  esac
done

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="$SKILL_DIR/assets"
cd "$ROOT"

# exact <path>: exists with exactly this spelling (macOS file systems ignore case, so -e alone can't tell).
exact() { [ -e "$1" ] && ls -1a "$(dirname "$1")" 2>/dev/null | grep -qxF "$(basename "$1")"; }
# legacy_of <path>: the pre-rename UPPER_SNAKE spelling (workflows/bug-fix.md -> workflows/BUG_FIX.md).
legacy_of() { echo "$(dirname "$1")/$(basename "$1" .md | tr 'a-z-' 'A-Z_').md"; }
conflicts=0; renames=""
place() { # place <src> <dest>
  src="$1"; dest="$2"; old="$(legacy_of "$dest")"
  if [ "$old" != "$dest" ] && exact "$old" && ! exact "$dest"; then
    echo "LEGACY   $old (old name of $dest; left untouched)"
    renames="$renames
  git mv '$old' '$old.tmp' && git mv '$old.tmp' '$dest'"
    return
  fi
  if [ -e "$dest" ]; then
    if cmp -s "$src" "$dest"; then echo "SKIP     $dest (exists, identical)"
    else echo "CONFLICT $dest (exists, differs; left untouched)"; conflicts=$((conflicts+1)); fi
    return
  fi
  echo "CREATE   $dest"
  if [ "$DRY" -eq 0 ]; then mkdir -p "$(dirname "$dest")"; cp "$src" "$dest"; fi
}

# Asset file names contain no spaces, so word-splitting the list is safe (and keeps the counter in this shell).
for rel in $(cd "$ASSETS/factory" && find . -type f -name '*.md' | sed 's|^\./||' | sort); do
  place "$ASSETS/factory/$rel" ".factory/$rel"
done

if [ "$ROUTER" -eq 1 ]; then
  place "$ASSETS/factory-router.SKILL.md" ".claude/skills/factory-router/SKILL.md"
fi

[ "$DRY" -eq 1 ] && echo "(dry run: nothing written)"
if [ -n "$renames" ]; then
  echo "legacy names found; with the owner's approval, rename them to the current names:$renames"
fi
if [ "$conflicts" -gt 0 ]; then
  echo "conflicts: $conflicts (resolve with the owner; never overwrite without approval)"
  exit 3
fi
exit 0

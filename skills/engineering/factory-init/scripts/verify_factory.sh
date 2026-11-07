#!/usr/bin/env bash
# verify_factory.sh — check that a repository's Software Factory is complete and internally consistent.
# Usage: verify_factory.sh [--relaxed] [--project-name NAME] [repo_root]
#
#   --relaxed           Missing standard project docs (product/, engineering/) are WARN, not FAIL.
#                       Use only when CLAUDE.md documents an adapted layout.
#   --project-name N    Also fail if N (case-insensitive) appears inside .factory/ (factory must stay project-agnostic).
#
# Checks: required files exist; CLAUDE.md wires in the factory; every backtick path and Markdown link
# in the factory, CLAUDE.md and project docs resolves; drift between .factory/ and the bundled snapshot.
# Exit code: 0 = no FAIL lines, 1 = at least one FAIL. Read-only.

set -u
RELAXED=0; NAME=""; ROOT="."
while [ $# -gt 0 ]; do
  case "$1" in
    --relaxed) RELAXED=1 ;;
    --project-name) NAME="${2:-}"; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) ROOT="$1" ;;
  esac
  shift
done
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 2

fails=0; warns=0
ok()   { echo "OK    $*"; }
fail() { echo "FAIL  $*"; fails=$((fails+1)); }
warn() { echo "WARN  $*"; warns=$((warns+1)); }
need() { if [ -e "$1" ]; then ok "$1"; else "$2" "missing: $1"; fi; }

echo "== 1. Factory files (.factory/)"
for rel in $(cd "$SKILL_DIR/assets/factory" && find . -type f -name '*.md' | sed 's|^\./||' | sort); do
  need ".factory/$rel" fail
done

echo "== 2. Project entry point and state"
need CLAUDE.md fail
need tasks/STATUS.md fail
need .claude/skills/factory-router/SKILL.md warn

echo "== 3. Standard project layout (workflows/NEW_PROJECT.md)"
lvl=fail; [ "$RELAXED" -eq 1 ] && lvl=warn
for f in product/PRODUCT_BRIEF.md product/PRD.md product/PERSONAS.md product/ROADMAP.md product/FEATURES.md \
         engineering/ARCHITECTURE.md engineering/TECH_STACK.md engineering/DATA_MODEL.md engineering/API_CONTRACTS.md \
         engineering/SECURITY_AND_PRIVACY.md engineering/DEVELOPMENT_GUIDE.md specs; do
  need "$f" $lvl
done
if ls engineering/adr/[0-9][0-9][0-9][0-9]-*.md >/dev/null 2>&1; then ok "engineering/adr/ has an ADR"; else $lvl "engineering/adr/ has no NNNN-*.md ADR"; fi

echo "== 4. CLAUDE.md wiring"
if [ -f CLAUDE.md ]; then
  for ref in .factory/core/AGENT_BEHAVIOR.md .factory/workflows/NEW_FEATURE.md .factory/workflows/BUG_FIX.md \
             .factory/workflows/REFACTORING.md .factory/workflows/CODE_REVIEW.md .factory/workflows/RESUME_WORK.md \
             .factory/core/DEFINITION_OF_DONE.md tasks/STATUS.md; do
    # Accept either the full path or the bare name next to a ".factory/workflows/" mention (table style).
    base=$(basename "$ref" .md)
    if grep -q "$ref" CLAUDE.md || { grep -q "$(dirname "$ref")/" CLAUDE.md && grep -qw "$base" CLAUDE.md; }; then
      ok "CLAUDE.md references $ref"
    else fail "CLAUDE.md does not reference $ref"; fi
  done
  if [ -e .claude/skills/factory-router/SKILL.md ]; then
    grep -q "factory-router" CLAUDE.md && ok "CLAUDE.md mentions factory-router" || warn "CLAUDE.md does not mention the factory-router skill"
  fi
  grep -qiE "(current )?phase" CLAUDE.md && ok "CLAUDE.md states a phase" || warn "CLAUDE.md has no phase section"
  if grep -nE '\{\{[A-Z_]+(:|\}\})' CLAUDE.md >/dev/null; then
    fail "CLAUDE.md still contains template placeholders:"; grep -nE '\{\{[A-Z_]+(:|\}\})' CLAUDE.md | head -10 | sed 's/^/      /'
  fi
fi

echo "== 5. Cross-references resolve"
# Candidate tokens: `backtick` spans and ](markdown links) that look like repo paths.
# Bases a relative path may be written against: repo root, the containing file's dir, .factory/, src/.
DOC_NAMES=$(find . -name '*.md' -not -path './node_modules/*' -not -path './.git/*' 2>/dev/null | sed 's|.*/||' | sort -u)
resolve() { # resolve <token> <containing file> -> 0 if found or not a repo path
  t="$1"; d=$(dirname "$2")
  case "$t" in
    */*) ;;
    # Bare file name (table shorthand such as `PRD.md` next to a `product/` column): exists anywhere?
    *.md) echo "$DOC_NAMES" | grep -qxF "$t"; return ;;
    *) [ -e "$t" ] || [ -e "$d/$t" ]; return ;;
  esac
  first="${t%%/*}"; rooted=0
  for b in . "$d" .factory src; do
    [ -e "$b/$t" ] && return 0
    [ -e "$b/$first" ] && rooted=1
  done
  [ "$first" = ".." ] && { [ -e "$d/$t" ]; return; }
  # First segment is not a directory anywhere: prose like `FR/NFR/BR` or `Asia/Jakarta`, not a path.
  return $rooted
}
check_file() { # check_file <file> <fail|warn>
  f="$1"; lv="$2"
  { grep -oE '`[^` ]+`' "$f" | tr -d '`'; grep -oE '\]\([^) #]+' "$f" | sed 's/^](//'; } 2>/dev/null | sort -u |
  while read -r t; do
    case "$t" in
      http*|mailto:*|*'<'*|*'>'*|*'*'*|*'{'*|*'$'*|*'…'*|*NNNN*|*'...'*|-*|@*|~*|/*) continue ;;
    esac
    t="${t%%#*}"; t="${t%%:*}"; t="${t%,}"; t="${t%.}"
    [ -z "$t" ] && continue
    # Only things that look like paths: contain a slash, or end in a doc/config extension.
    case "$t" in */*|*.md|*.json|*.yaml|*.yml|*.toml) ;; *) continue ;; esac
    l="$lv"
    # Factory docs may name project docs that do not exist yet; only factory-internal links must resolve.
    if [ "$l" = factory ]; then
      case "$t" in .factory/*|core/*|workflows/*|templates/*|../core/*|../workflows/*|../templates/*) l=fail ;; *) l=warn ;; esac
    fi
    # Bare file names are shorthand (e.g. `SPEC.md` before the first spec exists): never more than WARN.
    case "$t" in */*) ;; *) l=warn ;; esac
    resolve "$t" "$f" || echo "$l|$f -> $t"
  done
}
files=$(ls CLAUDE.md tasks/STATUS.md 2>/dev/null)
fdocs=$(ls .claude/skills/factory-router/SKILL.md 2>/dev/null; find .factory -name '*.md' 2>/dev/null)
docs=$(find product engineering -name '*.md' 2>/dev/null)
broken=$( { for f in $files; do check_file "$f" fail; done; for f in $fdocs; do check_file "$f" factory; done; for f in $docs; do check_file "$f" warn; done; } )
if [ -z "$broken" ]; then ok "no broken references"
else
  while IFS='|' read -r lv msg; do
    [ "$lv" = fail ] && fail "broken reference: $msg" || warn "unresolved reference (may be planned): $msg"
  done <<EOF
$broken
EOF
fi

echo "== 6. Factory hygiene and drift"
if [ -n "$NAME" ] && [ -d .factory ]; then
  hits=$(grep -rniw -- "$NAME" .factory 2>/dev/null | head -5)
  [ -z "$hits" ] && ok ".factory/ is free of '$NAME'" || { fail ".factory/ contains project-specific term '$NAME':"; echo "$hits" | sed 's/^/      /'; }
fi
if [ -d .factory ]; then
  drift=$(diff -rq "$SKILL_DIR/assets/factory" .factory 2>/dev/null | sed "s|$SKILL_DIR/assets/factory|<bundled>|g")
  [ -z "$drift" ] && ok ".factory/ matches the bundled snapshot" || { warn ".factory/ differs from the bundled snapshot (local edits or newer version):"; echo "$drift" | sed 's/^/      /'; }
fi

echo
echo "summary: $fails FAIL, $warns WARN"
[ "$fails" -eq 0 ]

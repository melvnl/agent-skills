#!/usr/bin/env bash
# validate-skills.sh: lint every SKILL.md and the repo wiring. Read-only.
# Checks:
#   - frontmatter starts on line 1 with `---` and is closed
#   - `name` exists, is kebab-case, matches the directory name, and is unique
#   - `description` exists and is <= 1024 characters
#   - every skill is listed in .claude-plugin/plugin.json and linked from README.md
#   - bundled copies in SYNCED_COPIES are byte-identical to their source
# Exit code: 0 = no FAIL, 1 = at least one FAIL.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

# "source:copy" pairs that must stay identical
SYNCED_COPIES=(
  "skills/engineering/factory-router/SKILL.md:skills/engineering/factory-init/assets/factory-router.SKILL.md"
)

fails=0
fail() { echo "FAIL  $*"; fails=$((fails+1)); }
ok()   { echo "OK    $*"; }

names_seen=" "
while IFS= read -r f; do
  rel_dir="$(dirname "$f")"
  dir="$(basename "$rel_dir")"
  if [ "$(head -n1 "$f")" != "---" ]; then fail "$f: frontmatter must start on line 1 with ---"; continue; fi
  if ! awk 'NR>1 && /^---$/{found=1; exit} END{exit !found}' "$f"; then fail "$f: frontmatter not closed"; continue; fi
  fm="$(awk 'NR==1{next} /^---$/{exit} {print}' "$f")"
  name="$(printf '%s\n' "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -n1)"
  desc="$(printf '%s\n' "$fm" | sed -n 's/^description:[[:space:]]*//p' | head -n1)"
  before=$fails

  if [ -z "$name" ]; then fail "$f: missing name"; else
    printf '%s' "$name" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$' || fail "$f: name '$name' is not kebab-case"
    [ "$name" = "$dir" ] || fail "$f: name '$name' does not match directory '$dir'"
    case "$names_seen" in *" $name "*) fail "$f: duplicate skill name '$name'" ;; esac
    names_seen="$names_seen$name "
  fi
  if [ -z "$desc" ]; then fail "$f: missing description"
  elif [ "${#desc}" -gt 1024 ]; then fail "$f: description is ${#desc} chars (max 1024)"; fi

  grep -q "\"./$rel_dir\"" .claude-plugin/plugin.json || fail "$rel_dir: missing from .claude-plugin/plugin.json"
  grep -q "($rel_dir/SKILL.md)" README.md || fail "$rel_dir: not linked from README.md"
  [ "$fails" -eq "$before" ] && ok "$f"
done < <(find skills -name SKILL.md | sort)

for pair in "${SYNCED_COPIES[@]}"; do
  src="${pair%%:*}"; copy="${pair##*:}"
  if cmp -s "$src" "$copy"; then ok "in sync: $copy"; else fail "drift: $copy differs from $src (copy the source over)"; fi
done

echo "summary: $fails FAIL"
[ "$fails" -eq 0 ]

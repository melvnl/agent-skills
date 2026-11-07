---
name: requirement-traceability
description: Maintains and checks the chain from source requirement to feature, acceptance criterion, task, code, test and report, with a deterministic checker for untraced or dangling ids. Use when specs, tasks or tests change, before closing a feature, or when asked whether every requirement is implemented and tested.
---

# Requirement Traceability

## Overview

Traceability answers two questions with evidence instead of memory: *is every requirement implemented and tested?* and *why does this code exist?* The Software Factory defines the chain (PRD `FR/NFR/BR` → feature `F-nn` → spec `AC-n` → task `T-n` → code → tests → report). This skill keeps it intact as work progresses and checks it with `trace_check.py`, a read-only script that finds dangling references and untraced requirements.

## When to use

- After `specification-decomposition`, to confirm every requirement has an owner and acceptance criteria.
- When a spec, task breakdown, or test suite changes.
- Before closing a feature (Definition of Done: "traceable by requirement ID"), and in Phase 6 of `PRD_TO_IMPLEMENTATION`.
- Asked "is everything covered?", "what implements FR-12?", or "why does this code exist?".

**When not to use:** writing the requirements or criteria themselves → `specification-decomposition`, `acceptance-criteria-engineering`.

## Inputs and context

1. A Software Factory layout: `product/PRD.md`, `product/FEATURES.md`, `specs/<F-ID>-<slug>/SPEC.md`, `tasks/<F-ID>-<slug>.md`. Without one, apply the same chain manually in the project's documents.
2. The project's test locations, if they differ from the checker's defaults.
3. The citation convention in tests: a comment or test name containing `F-07 AC-3` (also accepted: `F-07-AC-3`, `F-07/AC-3`). Code comments cite requirement ids (`# BR-4`), as `CODING_STANDARDS` requires.

## Process

1. **Keep ids in the tables.** Requirements live in PRD table rows; features list their requirement ids in `FEATURES.md`; each spec's *Verifies* column lists what each AC verifies; each task's *Covers* column lists what it implements. Ranges (`FR-21..FR-27`) are fine.
2. **Cite in code and tests while working**, not afterwards: a business-rule implementation cites its `BR-n`; each test that verifies an acceptance criterion cites `<F-ID> AC-n`.
3. **Run the checker**:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/trace_check.py" --root .
   python3 "${CLAUDE_SKILL_DIR}/scripts/trace_check.py" --root . --tests "src/**/tests/*.py"   # custom test globs
   python3 "${CLAUDE_SKILL_DIR}/scripts/trace_check.py" --root . --json                      # machine-readable
   ```

4. **Fix FAILs at the source.** Define the missing id, assign the unowned requirement to a feature, add the missing acceptance criterion, or correct the typo. Never delete a reference just to make the check pass.
5. **Triage WARNs.** An AC no test cites is either untested (write the test), verified manually (say so in the spec's *Method* column and the report), or cited in a form the checker doesn't see (fix the citation).
6. **Record the result** in the implementation report: the summary line and any accepted warnings with reasons.

### What the checker enforces

| Level | Condition |
|---|---|
| FAIL | A feature, spec or task references an id not defined in `PRD.md` |
| FAIL | A defined FR, NFR or BR is owned by no feature (deprecated ids and `Q-n` exempt) |
| FAIL | An acceptance criterion verifies nothing |
| FAIL | A spec-level requirement (`F-07-FR-1`) has no acceptance criterion |
| WARN | An acceptance criterion is cited by no test |
| WARN | A task covers nothing |

It does not judge whether a test *really* verifies its criterion. That is code review's job.

## Output

The checker's report, plus a traceability note in the implementation report:

```markdown
### Traceability
trace_check: defined=42, acceptance_criteria=31, fail=0, warn=2
Accepted warnings: F-07 AC-9 verified manually (bureau sandbox unavailable; evidence in report §3).
```

## Verification

- [ ] `trace_check.py` exits 0 (no FAIL), and the run is shown, not described.
- [ ] Every remaining WARN is resolved or explicitly accepted with a reason.
- [ ] Code implementing business rules cites `BR-n`; tests verifying acceptance criteria cite `<F-ID> AC-n`.

## Escalation

Ask when: fixing a FAIL requires changing approved requirements or acceptance criteria; a requirement seems to belong to no feature (scope question for the owner); or the project uses a different id scheme (agree on a mapping before running the checker).

## References

- `scripts/trace_check.py`: the checker (usage in its header). Tests: `scripts/tests/test_trace_check.py`, run with `python3 -m unittest discover -s scripts/tests`.

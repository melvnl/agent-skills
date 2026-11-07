---
name: specification-decomposition
description: Turns analyzed requirements into stable requirement ids, domain groups, a feature catalog and atomic, independently deliverable feature specs with traceability. Use after a PRD has been analyzed and its blocking questions resolved, or when a large spec must be split into buildable features.
---

# Specification Decomposition

## Overview

An analyzed PRD is still one large document. Implementation needs small, independently deliverable units, each with its own contract. This skill assigns stable ids, groups requirements by domain, cuts them into atomic feature specifications, and records how every spec traces back to the source. It uses the Software Factory formats (`PRD`, `FEATURES`, `FEATURE_SPEC`) so the rest of the factory works on the result unchanged.

## When to use

- After `prd-analysis`, once the owner has resolved or explicitly accepted its Blocking issues.
- A single spec or epic is too large to design and review in one sitting.
- Phase 2 of the Software Factory `PRD_TO_IMPLEMENTATION` workflow.

**When not to use:** the source hasn't been analyzed → `prd-analysis` first. Writing the acceptance criteria inside a spec → `acceptance-criteria-engineering`. Breaking one spec into implementation tasks → `planning-and-task-breakdown`.

## Inputs and context

1. The analysis (`product/analysis/<source>-analysis.md`) and its owner decision log.
2. Existing `product/PRD.md` and `product/FEATURES.md`: their id sequences, groups and phases. **New ids continue the existing sequence.**
3. Existing `specs/`: extend an existing feature instead of creating a parallel one.
4. The roadmap and phase plan (`product/ROADMAP.md`), if any.
5. Templates: `.factory/templates/PRD.md`, `.factory/templates/FEATURE_SPEC.md`.

## Process

1. **Assign stable ids** to every accepted statement from the analysis: `FR-n`, `NFR-n`, `BR-n`, and `Q-n` for open questions. Continue the existing numbering; never renumber or reuse an id; deprecate instead. Keep each id's source reference (analysis row → source section).
2. **Group by domain or capability** (e.g. *Application intake*, *Eligibility decision*, *Notifications*). Groups follow the domain language from the analysis glossary, not the PRD's chapter order.
3. **Cut features.** A feature (`F-nn`) is the smallest slice that delivers a user-visible or operator-visible outcome and can be verified end to end. Apply the splitting heuristics in [references/decomposition-rules.md](references/decomposition-rules.md). Target 3–10 FRs per feature; split larger ones.
4. **Check atomicity** for each candidate feature: one primary actor goal; independently testable; its design fits one review; no circular dependency with another feature. Shared infrastructure that several features need becomes its own enabling feature, ordered first.
5. **Map dependencies** between features (data, API, sequencing) and assign phases where a roadmap exists. Flag a later-phase dependency of an earlier-phase feature as a conflict.
6. **Write or extend the documents**:
   - `product/PRD.md`: new requirements in their groups, with a change-log entry.
   - `product/FEATURES.md`: each feature with linked requirement ids, phase, dependencies, status ⬜.
   - `specs/<F-ID>-<slug>/SPEC.md` from `FEATURE_SPEC`: problem, goals, non-goals, user stories, feature-scoped requirements tracing to PRD ids, edge cases, dependencies, open questions. Status **Draft**.
7. **Write the acceptance criteria** for each spec with `acceptance-criteria-engineering`.
8. **Record traceability**: each spec's requirement rows cite PRD ids; each PRD id appears in exactly one owning feature (a requirement shared by two features is either split, or owned by one and referenced by the other). Run `requirement-traceability` to check coverage.
9. ⏸ **Gate:** present the feature catalog, dependency map and specs for approval. Specs change from *Draft* to *Approved* only with owner approval.

## Output

- Updated `product/PRD.md` and `product/FEATURES.md` (with change-log entries).
- One `specs/<F-ID>-<slug>/SPEC.md` per feature, status *Draft*.
- A decomposition summary for the approval gate:

```markdown
| Feature | Requirements | Depends on | Phase | Notes |
|---|---|---|---|---|
| F-07 Eligibility decision | FR-21..FR-27, BR-4..BR-9, NFR-3 | F-05 | 1 | rule versioning in scope |
Unassigned requirements: none | FR-30 (Q-3 pending)
```

Without a Software Factory, produce the same artifacts in the project's documentation location, or propose running `factory-init`.

## Verification

- [ ] Every accepted analysis statement has exactly one stable id; no id was renumbered or reused.
- [ ] Every FR, NFR and BR is owned by exactly one feature, or listed as unassigned with a reason.
- [ ] Each feature passes the atomicity checks; none exceeds ~10 FRs without a recorded reason.
- [ ] The dependency map has no cycles; phase conflicts are flagged.
- [ ] Each spec traces its requirements to PRD ids and has acceptance criteria.
- [ ] `requirement-traceability` reports no untraced requirement.

## Escalation

Ask when: a requirement can't be assigned without a product decision (which feature owns a cross-cutting rule); splitting would change the delivery order or phase plan; an open question blocks a whole feature; or an extension would alter an already-approved spec's acceptance criteria (needs approval and a change-log entry).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "One big spec is easier to keep consistent." | It is impossible to review, design or deliver incrementally. Consistency comes from ids and traceability. |
| "I'll renumber to keep it tidy." | Ids are references from code, tests and reports. Renumbering breaks every one. |
| "Infrastructure isn't a feature." | When three features need it, it is an enabling feature with its own spec and order. |

## References

- [references/decomposition-rules.md](references/decomposition-rules.md): splitting heuristics, id conventions, worked example.

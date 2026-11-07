# Workflow: New Feature

> **Scope:** Project-agnostic. Use for any new user-visible capability or meaningful extension of an existing one.

## Purpose

Turn a feature request into working, tested, documented software through explicit specification, design, and incremental implementation.

## Entry conditions

- The request is classified as a new or extended capability (not a bug, refactor, or question).
- No existing spec already covers it (otherwise extend that spec).
- For features built from a large requirements document, `PRD_TO_IMPLEMENTATION.md` runs first and hands off here per feature.

## Inputs

- The feature request (from a human, roadmap item, or feature catalog entry).
- Project docs: PRD, feature catalog, roadmap, architecture, data model, contracts, security doc.
- Existing code and tests in the affected area.

## Outputs

| Artifact | Template | Conventional location |
|---|---|---|
| Feature specification | `templates/FEATURE_SPEC.md` | `specs/<feature-id>-<slug>/SPEC.md` |
| Technical design | `templates/TECHNICAL_DESIGN.md` | `specs/<feature-id>-<slug>/DESIGN.md` |
| Task breakdown | `templates/TASK_BREAKDOWN.md` | `tasks/<feature-id>-<slug>.md` |
| ADR (if a significant decision is made) | `templates/ARCHITECTURE_DECISION_RECORD.md` | `engineering/adr/NNNN-<slug>.md` |
| Code + tests | — | Source tree |
| Implementation report | `templates/IMPLEMENTATION_REPORT.md` | `tasks/reports/<feature-id>-<slug>.md` |

## Execution steps

```mermaid
flowchart TD
  U[1 Understand] --> A[2 Analyze context] --> S[3 Spec + acceptance criteria]
  S -->|approval| D[4 Technical design] -->|approval if significant| T[5 Task breakdown]
  T --> I[6 Implement increment] --> V[7 Verify] --> I
  V --> R[8 Code review] --> P[9 Report + docs] --> H[Human approval]
```

1. **Understand the request.** Restate it in one paragraph. Identify the user, the problem, and the expected outcome. List ambiguities.
2. **Analyze existing requirements and architecture.** Read the PRD/feature catalog entry, related specs, architecture, data model, and the code in the affected area. Note constraints and conflicts.
3. **Produce or update the feature specification.** Fill `FEATURE_SPEC.md`: problem, goals, non-goals, user stories, functional/non-functional requirements (with IDs), edge cases, dependencies, open questions.
4. **Define acceptance criteria.** Given/When/Then, each mapped to requirement IDs and to a planned verification (unit/integration/E2E/manual).
   - 🔒 **Gate: spec approval** — human approves the spec before design is finalized when the feature changes product behavior.
5. **Produce the technical design.** Fill `TECHNICAL_DESIGN.md`: architecture, components, data model changes, contracts, data flows, failure scenarios, the **observability plan**, security, testing strategy, trade-offs. Write an ADR for significant decisions. Business fallbacks in the failure scenarios need owner approval.
6. **Break down into tasks.** Fill `TASK_BREAKDOWN.md`. Each task is small (≈ ≤ half a day), independently verifiable, and keeps the build green. Start with a thin end-to-end slice; then add vertical slices. Each task names its tests and its share of the observability plan.
7. **Implement incrementally, as a loop per task:** select → load only the needed context → write the failing test → implement → add the instrumentation assigned to the task → run targeted tests → on failure, diagnose before fixing → verify against the task's done-when → checkpoint (task status, `tasks/STATUS.md` next action and last verification). Do not start the next task with a red build. **Stop and report** after three failed fixes on the same hypothesis, two iterations without progress, or when a fix would change the spec, contracts, or data model.
8. **Run automated verification.** Run all quality gates (`TESTING_STANDARDS.md` § 10). Record actual results.
9. **Perform independent review** per `CODE_REVIEW.md`: a self-review first, then review and verification by someone other than the implementer (another agent role or a human). Add specialist reviews where the change warrants them: `OBSERVABILITY_REVIEW.md` for backend changes, `SECURITY_REVIEW.md` for endpoints, integrations, and auth, and the `FINTECH_FEATURE.md` overlay gates for financial decision logic.
10. **Produce the implementation report** (including its *Instrumentation* section) and update docs: spec/design to match reality, feature catalog status, data model/contracts/ADRs if changed, project status.

## Quality gates

| Gate | Passes when |
|---|---|
| Spec ready | Every requirement is testable; every acceptance criterion maps to a verification method; open questions are non-blocking or resolved. |
| Design ready | Every functional requirement is addressed by a component; data model and contract changes are explicit; security impact assessed. |
| Increment done | Tests for the increment pass; lint/type-check pass. |
| Feature done | `DEFINITION_OF_DONE.md` fully satisfied; reviews by someone other than the implementer recorded. |

## Exit conditions

- Feature done gate passed, implementation report written, and status files updated; **or**
- Work stopped at a gate or stop condition, with the reason, the state, and the next action recorded in `tasks/STATUS.md`.

## Human approval required

- Spec (when product behavior changes) and any change to acceptance criteria.
- Design decisions recorded as ADRs; data model migrations; contract or security changes.
- Merge to the main branch.

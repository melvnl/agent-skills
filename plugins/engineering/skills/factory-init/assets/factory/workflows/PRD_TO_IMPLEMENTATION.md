# Workflow: PRD to Implementation

> **Scope:** Project-agnostic. Use when a large product requirements document (often drafted or expanded with AI) is the starting point for several features.

## Purpose

Turn a large requirements document into verified, released features without losing traceability or building on contradictions: analyze it, decompose it into atomic specs, design, plan, implement in loops, verify independently, and release with human approval.

## Entry conditions

- A source document exists and its owner is known.
- The project has the Software Factory layout (or the owner agrees to set it up first).

## Inputs

- The source document(s), unmodified.
- Existing product and engineering documents, specs, and code.

## Outputs (all in the standard factory locations)

| Phase | Artifacts |
|---|---|
| 1 | `product/sources/<doc>` (unmodified), `product/analysis/<doc>-analysis.md` |
| 2 | `product/PRD.md` ids, `product/FEATURES.md`, `specs/<F-ID>-<slug>/SPEC.md` |
| 3 | `specs/<F-ID>-<slug>/DESIGN.md` (incl. failure scenarios and observability plan), ADRs |
| 4 | `tasks/<F-ID>-<slug>.md` |
| 5 | code, tests, task status, `tasks/STATUS.md` checkpoints |
| 6 | review records, traceability check results |
| 7 | `tasks/reports/<F-ID>-<slug>.md` with release and rollback notes |

## Execution steps

### Phase 1: Intake and analysis

1. Preserve the source unmodified; inventory its sections with stable references.
2. Extract functional and non-functional requirements, business rules, entities, and actors, each with its source reference.
3. Detect contradictions, ambiguities, duplicates, missing NFRs, untestable statements, and generated-text artifacts; rate each.
4. 🔒 **Gate:** the owner resolves blocking issues (or accepts them as open, with what they block).

### Phase 2: Specification decomposition

5. Assign stable ids (`FR`, `NFR`, `BR`, `Q`), continuing existing sequences; group by domain.
6. Cut atomic, independently verifiable features; map dependencies and phases.
7. Write draft feature specs with acceptance criteria; establish traceability (every requirement owned by one feature).
8. 🔒 **Gate:** the owner approves the feature catalog and specs.

### Phase 3: Technical design (per feature)

9. Analyze the existing architecture; identify impacted services, API and data changes, and integration boundaries.
10. Define failure scenarios, resilience behavior, and the **observability plan**; record significant decisions as ADRs.
11. 🔒 **Gate:** design approval when the feature is substantial (per `NEW_FEATURE.md`).

### Phase 4: Task planning (per feature)

12. Decompose into small tasks with dependencies, execution order, tests, instrumentation, and done-when conditions.

### Phase 5: Implementation loops (per task)

13. Select task → load context → implement test-first → add the task's instrumentation → run targeted tests → evaluate → diagnose → fix → verify → **checkpoint** → next task, with the stop conditions in `NEW_FEATURE.md` step 7.

### Phase 6: Independent verification (per feature)

14. Run regression suites and quality gates; verify each acceptance criterion against evidence.
15. Review security (`SECURITY_REVIEW.md`), data integrity, observability (`OBSERVABILITY_REVIEW.md`), including correlation propagation and sensitive logging; review migrations (`DATABASE_MIGRATION.md`). Financial features add the `FINTECH_FEATURE.md` gates.
16. Run the traceability check; resolve failures at the source.
17. Reviewers are never the implementer.

### Phase 7: Final review

18. Review the complete diff against the specs; list unresolved issues with severity and owner.
19. Write release notes and rollback considerations in the implementation report.
20. 🔒 **Gate:** human approval before any production deployment.

## Quality gates

| Gate | Passes when |
|---|---|
| Analysis complete | Every section read; every statement referenced; blocking issues resolved or accepted |
| Specs ready | Every requirement owned by one feature; acceptance criteria testable and traced |
| Feature done | `NEW_FEATURE.md` feature-done gate plus Phase 6 reviews |
| Release ready | No open Blocker; rollback documented; approval recorded |

## Exit conditions

- All in-scope features done and released with approval; **or** stopped at a gate, with `tasks/STATUS.md` naming the phase, feature, decision needed, and next action.

## Human approval required

- Resolution of blocking analysis issues; the feature catalog and specs; substantial designs and ADRs.
- Migrations, dependency additions, contract changes (per their workflows).
- Production deployment.

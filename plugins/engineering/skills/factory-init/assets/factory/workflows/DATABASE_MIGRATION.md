# Workflow: Database Migration

> **Scope:** Project-agnostic. Applies to schema changes, data migrations, backfills, and index or constraint changes on shared environments.

## Purpose

Change schemas and data without outages, data loss, or code that breaks against the schema it meets, with a plan and evidence a reviewer can check before anything runs on shared data.

## Entry conditions

- The target schema is defined in an approved design (or this is a reviewed data fix with an approved scope).
- Table facts are known: row counts, sizes, write rates (or measured during step 1).

## Inputs

- The design's data model changes and the project's data model document.
- The migration framework and how migrations run in deploys.
- Engine and version; the team's tools for large online changes.

## Outputs

- A migration plan: steps, deploys, compatibility per step, locking behavior or online tool, expected duration, validation queries, rollback or forward-fix per step.
- Migration files and backfill jobs.
- Rehearsal evidence: duration, lock behavior, before/after validation.

## Execution steps

1. **Classify** the change: additive, transformative, or destructive.
2. **Sequence** with expand → migrate → contract whenever two code versions can meet the schema during a deploy. Each step is a separate migration and deploy.
3. **Choose the execution method** for large tables (online algorithm or tool) and state its locking behavior, including metadata locks blocked by long transactions.
4. **Write migrations** with one risky operation each; review the generated SQL; provide reverse operations or an explicit forward-fix plan. Never edit an applied migration.
5. **Write backfills** as chunked, idempotent, resumable, throttled jobs with a dry-run mode, separate from schema changes.
6. **Define validation**: counts, sums of critical columns, invariant checks, and sampled row comparisons, before and after.
7. **Rehearse** on a production-like copy (engine version, realistic size): record duration, locks, replication lag, and validation results.
8. **Review**: an independent reviewer checks the plan, files, and rehearsal evidence.
9. **Run** in the shared environment only after approval, by whoever the project designates, with monitoring and a stop criterion.
10. **Verify** with the validation queries and record the results in the implementation report.

If the `database-migrations` and `mysql-engineering` skills or the `database-engineer` agent are available, use them.

## Quality gates

| Gate | Passes when |
|---|---|
| Compatibility | Every intermediate state works with adjacent code versions |
| Locking | Large-table steps name their algorithm or tool and lock behavior |
| Rehearsal | Rehearsal evidence recorded, or the gap explicitly accepted by the owner |
| Validation | Before/after results match expectations |

## Exit conditions

- All steps applied and validated, with evidence recorded; **or** stopped at a gate with state and next step recorded.

## Human approval required

- Every run outside local or disposable databases.
- Destructive steps: drops, narrowing, `NOT NULL` or unique constraints over existing data.
- Backfills touching financial or personal data.
- Accepting a missing rehearsal.

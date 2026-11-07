---
name: database-migrations
description: Plans, writes and verifies schema and data migrations that stay compatible across deploys: expand-migrate-contract, safe column, index and constraint changes on large MySQL tables, batched idempotent backfills, Django migration review, and a rollback or forward-fix plan. Use when creating or reviewing a migration, backfill, rename, column drop, or index change.
---

# Database Migrations

## Overview

A migration runs against live data, while old and new application versions coexist during a deploy, often on tables too large to lock. Most migration incidents are locking outages, half-applied changes, or code that breaks against the schema it meets. This skill sequences schema changes so every intermediate state works, makes data changes resumable, and proves the plan on realistic data before production.

## When to use

- Creating, reviewing, or running a schema or data migration.
- Renaming or dropping columns or tables, changing types or nullability, adding constraints or indexes, backfilling data.
- The Software Factory `DATABASE_MIGRATION` workflow.

**When not to use:** deciding the target schema → `database-design`. Engine internals (online DDL algorithms, locks) are summarized here and detailed in `mysql-engineering`.

## Inputs and context

1. The target schema and why (spec/design, `DATA_MODEL.md`).
2. **Table facts**: row counts, size, write rate, and which code paths read and write it. Ask for production numbers if you can't measure them; "small" must be a number.
3. Engine and version (MySQL 5.7 vs 8.0 point release, Aurora version), and the tools the team uses for large changes (native online DDL, `gh-ost`, `pt-online-schema-change`).
4. The migration framework (Django migrations, Alembic, Flyway, raw SQL) and how migrations run in deploys (before or after code rollout, automatically or manually).
5. Existing migration history: applied migrations are immutable.

## Process

1. **Classify the change** ([references/migration-patterns.md](references/migration-patterns.md)): additive (new table, nullable column, index), transformative (type change, backfill, rename), or destructive (drop, narrow, add `NOT NULL` to existing data, unique constraint on dirty data).
2. **Sequence with expand → migrate → contract** whenever old code could meet the new schema, or new code the old one:
   - *Expand*: add new structures compatibly (nullable or defaulted columns, new tables). Deploy.
   - *Migrate*: dual-write or backfill; switch reads; verify. Deploy.
   - *Contract*: stop using the old structure in code, deploy, then remove it in a later migration.
   Each step is its own migration and deploy; each intermediate state works with both adjacent code versions.
3. **Make schema changes non-blocking** on large tables: check the DDL algorithm (MySQL `ALGORITHM=INSTANT/INPLACE`, `LOCK=NONE`) and metadata-lock behavior, or use the team's online schema change tool. Note that even online DDL waits for a metadata lock, which a long-running transaction can block, stalling all queries behind it. Set a lock wait timeout for the DDL session.
4. **Write backfills as resumable batch jobs**: chunked by primary key ranges, idempotent (safe to re-run), throttled, with progress logged, and outside the schema migration transaction. Never one giant `UPDATE` on a large table.
5. **Mind transactions.** MySQL DDL causes an implicit commit, so a Django migration mixing several operations on MySQL **is not atomic**: a failure can leave it half-applied. Keep one risky operation per migration; data migrations (`RunPython`) separate from schema changes.
6. **Review generated migrations** instead of trusting them: Django `makemigrations` can turn a rename into drop + add (data loss) and emit table rebuilds. Read `sqlmigrate <app> <migration>` output; use `migrate --plan`; use `SeparateDatabaseAndState` when the model and database must move separately.
7. **Provide reversibility honestly.** Give `RunPython` a reverse function, or `RunPython.noop` with a comment when reversal is impossible. For destructive steps, the rollback plan is usually a **forward fix plus a backup or snapshot**, stated explicitly.
8. **Rehearse** on a production-like copy (same engine version, realistic size): measure duration, lock behavior, and replication lag; verify data afterwards with checks (counts, null counts, checksums on samples).
9. **Never edit an applied migration**; add a new one. Resolve ordering conflicts with a merge migration, not by rewriting history.
10. ⏸ **Approval**: destructive or long-running migrations, and anything touching financial or personal data, need explicit owner approval with the rehearsal results.

## Output

A migration plan, plus the migration files:

```markdown
### Migration plan: applications.decision_reason
| Step | Change | Deploy | Compatible with | Risk / duration (rehearsal) |
|---|---|---|---|---|
| 1 expand | ADD COLUMN decision_reason VARCHAR(64) NULL (INSTANT) | release N | code N-1, N | <1 s, metadata lock only |
| 2 migrate | code writes the column; backfill job in 5k-row chunks | release N+1 | N, N+1 | ~40 min at 2M rows, throttled |
| 3 contract | none (no old column) | none | none | none |
Verification: null count 0 after backfill for decided rows; sample checksum matches.
Rollback: step 1 reversible (drop column); step 2 forward-fix only.
```

## Verification

- [ ] Every intermediate state works with the code versions deployed around it.
- [ ] The DDL algorithm or tool for large tables is stated, and lock behavior checked.
- [ ] Backfills are chunked, idempotent, resumable, and throttled.
- [ ] Generated SQL was read (`sqlmigrate` or equivalent); no accidental drop + add.
- [ ] Rehearsed on a production-like copy, with measured duration and post-checks; or the gap is stated.
- [ ] Reverse or forward-fix plan written; applied migrations untouched.
- [ ] Approval obtained for destructive or long-running steps.

## Escalation

Always ask before: dropping or narrowing columns or tables; adding `NOT NULL` or unique constraints over existing data; any migration without a rehearsal on realistic data; backfills that touch financial or personal data; or running anything against production yourself (never do that unasked).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's just adding an index." | On a large hot table, without an online algorithm, it blocks writes. Check. |
| "Django migrations are transactional." | Not on MySQL: DDL commits implicitly. |
| "Rename the column in one migration." | Old code still running during the deploy queries the old name and fails. Expand, migrate, contract. |
| "The backfill is a one-liner." | A single UPDATE on millions of rows holds locks, bloats undo logs, and lags replicas. Batch it. |

## References

- [references/migration-patterns.md](references/migration-patterns.md): safe patterns per change type, MySQL DDL notes, backfill template.

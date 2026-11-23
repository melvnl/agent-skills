---
name: database-migrations
description: Plans, writes and verifies schema and data migrations that stay compatible across deploys on any engine and migration tool: expand-migrate-contract, non-blocking column, index and constraint changes on large tables, batched idempotent backfills, review of generated SQL, and a rollback or forward-fix plan. Use when creating or reviewing a migration, backfill, rename, column drop, or index change.
---

# Database Migrations

## Overview

A migration runs against live data, while old and new application versions coexist during a deploy, often on tables too large to lock. Most migration incidents are locking outages, half-applied changes, or code that breaks against the schema it meets. This skill sequences schema changes so every intermediate state works, makes data changes resumable, and proves the plan on realistic data before production.

## When to use

- Creating, reviewing, or running a schema or data migration, with any tool (Django, Alembic, MikroORM/Medusa, Prisma, TypeORM, Knex, Flyway, raw SQL).
- Renaming or dropping columns or tables, changing types or nullability, adding constraints or indexes, backfilling data.
- The Software Factory `DATABASE_MIGRATION` workflow.

**When not to use:** deciding the target schema → `database-design`. Query plans and locking semantics outside migrations → `database-queries-and-concurrency`.

## Inputs and context

1. The target schema and why (spec/design, `DATA_MODEL.md`).
2. **Table facts**: row counts, size, write rate, and which code paths read and write it. Ask for production numbers if you can't measure them; "small" must be a number.
3. **Engine and version**, then read its section in [references/engine-notes.md](references/engine-notes.md): which DDL is instant, online, or blocking, and whether DDL is transactional.
4. **The migration tool** and how migrations run in deploys (before or after code rollout, automatically or manually); read its section in [references/tool-notes.md](references/tool-notes.md).
5. Existing migration history: applied migrations are immutable.

## Process

1. **Classify the change** ([references/migration-patterns.md](references/migration-patterns.md)): additive (new table, nullable column, index), transformative (type change, backfill, rename), or destructive (drop, narrow, add `NOT NULL` to existing data, unique constraint on dirty data).
2. **Sequence with expand → migrate → contract** whenever old code could meet the new schema, or new code the old one:
   - *Expand*: add new structures compatibly (nullable or defaulted columns, new tables). Deploy.
   - *Migrate*: dual-write or backfill; switch reads; verify. Deploy.
   - *Contract*: stop using the old structure in code, deploy, then remove it in a later migration.
   Each step is its own migration and deploy; each intermediate state works with both adjacent code versions.
3. **Make schema changes non-blocking** on large tables, using the engine's online path (concurrent index builds, `NOT VALID` constraints validated later, instant column adds) or the team's online schema change tool. Even online DDL needs a brief exclusive lock; a long-running transaction can block it and queue all traffic behind it. Set a short lock timeout for the migration session.
4. **Write backfills as resumable batch jobs**: chunked by primary-key ranges, idempotent, throttled, with progress logged, and outside the schema migration transaction. Never one giant `UPDATE` on a large table.
5. **Know whether DDL is transactional.** PostgreSQL DDL is (except operations like `CREATE INDEX CONCURRENTLY`, which can't run inside a transaction); MySQL DDL commits implicitly, so a multi-operation migration can be left half-applied. Keep one risky operation per migration; data changes separate from schema changes.
6. **Read the generated SQL** instead of trusting the generator. Generators turn renames into drop + add (data loss), emit table rebuilds, and drop things they don't know about. Use the tool's SQL preview or dry run.
7. **Provide reversibility honestly.** Give data migrations a reverse step, or mark them irreversible with a comment. For destructive steps, the rollback plan is usually a **forward fix plus a backup or snapshot**, stated explicitly.
8. **Rehearse** on a production-like copy (same engine version, realistic size): measure duration, lock behavior and replication lag; verify data afterwards (counts, null counts, sample checksums).
9. **Never edit an applied migration**; add a new one. Resolve ordering conflicts with the tool's merge mechanism, not by rewriting history.
10. ⏸ **Approval**: destructive or long-running migrations, and anything touching financial or personal data, need explicit owner approval with the rehearsal results.

## Output

A migration plan, plus the migration files:

```markdown
### Migration plan: order.fulfillment_status
| Step | Change | Deploy | Compatible with | Risk / duration (rehearsal) |
|---|---|---|---|---|
| 1 expand | ADD COLUMN fulfillment_status text NULL | release N | code N-1, N | <1 s, brief lock |
| 2 migrate | code writes the column; backfill job in 5k-row chunks | release N+1 | N, N+1 | ~40 min at 2M rows, throttled |
| 3 contract | SET NOT NULL via validated CHECK, then drop old column | release N+2 | N+1, N+2 | validation scan, no write lock |
Verification: null count 0 after backfill; sample checksum matches.
Rollback: step 1 reversible (drop column); step 2 forward-fix only.
```

## Verification

- [ ] Every intermediate state works with the code versions deployed around it.
- [ ] The DDL path or tool for large tables is stated, and lock behavior checked for this engine version.
- [ ] Backfills are chunked, idempotent, resumable, and throttled.
- [ ] Generated SQL was read; no accidental drop + add or unexpected rebuild.
- [ ] Rehearsed on a production-like copy, with measured duration and post-checks; or the gap is stated.
- [ ] Reverse or forward-fix plan written; applied migrations untouched.
- [ ] Approval obtained for destructive or long-running steps.

## Escalation

Always ask before: dropping or narrowing columns or tables; adding `NOT NULL` or unique constraints over existing data; any migration without a rehearsal on realistic data; backfills that touch financial or personal data; or running anything against production yourself (never do that unasked).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's just adding an index." | On a large hot table, without the online path, it blocks writes. Check. |
| "Migrations are transactional." | Not on MySQL, and not for concurrent index builds on PostgreSQL. |
| "Rename the column in one migration." | Old code still running during the deploy queries the old name and fails. Expand, migrate, contract. |
| "The generator wrote it, so it's right." | Generators turn renames into drops. Read the SQL. |

## References

- [references/migration-patterns.md](references/migration-patterns.md): safe pattern per change type and a backfill template.
- [references/engine-notes.md](references/engine-notes.md): read for the target engine: PostgreSQL and MySQL/Aurora DDL locking and online paths.
- [references/tool-notes.md](references/tool-notes.md): read for the migration tool in use: Django, Alembic, MikroORM (Medusa), Prisma, TypeORM.

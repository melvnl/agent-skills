---
name: database-queries-and-concurrency
description: Makes relational queries fast and concurrent writes correct on any SQL engine (PostgreSQL, MySQL, Aurora): plans verified with EXPLAIN, query-derived indexes, keyset pagination, batched writes, lost-update prevention, locking reads and SKIP LOCKED, deadlock retries, uniqueness as idempotency, and replica lag. Use when writing or tuning SQL or ORM queries, handling concurrent updates, or diagnosing slow queries, deadlocks or lock waits.
---

# Database Queries and Concurrency

## Overview

Queries that pass tests on small data time out at volume, and concurrent read-modify-write code silently loses updates. Both come from assuming how the engine behaves instead of checking: what plan it picks, what isolation level is in force, what a locking read actually locks. This skill verifies plans with `EXPLAIN` on realistic data and picks a concurrency pattern that is correct under the engine's real semantics, whatever ORM sits on top.

## When to use

- Writing or optimizing queries and indexes, through raw SQL or any ORM (Django ORM, SQLAlchemy, MikroORM, Prisma, TypeORM, Knex).
- Implementing concurrent updates, counters, stock or balance changes, job claiming, uniqueness, or idempotency in the database.
- Diagnosing slow queries, deadlocks, lock wait timeouts, or replica lag.

**When not to use:** modeling tables and constraints → `database-design`. Rolling out schema changes → `database-migrations`. Whole-request latency where the database may not be the bottleneck → `performance-engineering` first.

## Inputs and context

1. **Engine and version**. Features and defaults differ; read the engine file before relying on any of them: [references/postgresql.md](references/postgresql.md) or [references/mysql.md](references/mysql.md).
2. Session settings that change behavior: isolation level, statement and lock timeouts, collation, strict modes.
3. The table definition, its indexes, and approximate row count. "Small" must be a number.
4. **The SQL actually executed**, captured from query logs or the ORM's debug output, with realistic parameters. ORM code is not the query.
5. Topology: primary and replicas, connection pooler (PgBouncer, RDS Proxy) and its mode, how the app routes reads.

## Process

### Queries and indexes

1. **Get the real SQL and its plan.** Run `EXPLAIN` on realistic data; use the executing form (`EXPLAIN ANALYZE`) only on a non-production copy or with care, because it runs the query. Look for full scans of large tables, sorts and temporary structures, and estimated rows far from actual rows.
2. **Design composite indexes for the query**: equality predicates first, then one range or the `ORDER BY` columns; the leftmost prefix must match. Consider covering indexes for hot reads. Every index costs writes, so map each one to a named query (`database-design`).
3. **Avoid index killers**: functions on indexed columns (`DATE(created_at) = ...` → a range on `created_at`, or an expression index); implicit type conversion between column and parameter; leading wildcards (`LIKE '%x'`); `OR` across different columns.
4. **Kill N+1 at the ORM layer**: eager-load relations used in loops, batch lookups by id, and pin the query count of list endpoints in a test.
5. **Paginate with keysets** (`WHERE (created_at, id) > (?, ?) ORDER BY created_at, id LIMIT 50`), not large `OFFSET`s, which read and discard every skipped row.
6. **Don't count what you don't need.** Exact `COUNT(*)` on a large table is a scan on both engines. Use `EXISTS` for presence; approximate or maintained counts for dashboards.
7. **Batch large writes and deletes** by primary-key ranges in small transactions. One huge `UPDATE` or `DELETE` holds locks for its whole duration, bloats undo or dead tuples, and lags replicas.

### Concurrency

8. **Know the isolation level in force.** PostgreSQL defaults to READ COMMITTED; InnoDB to REPEATABLE READ with gap locks. The same code has different races and different blocking on each. Check the session, not the documentation's default.
9. **Prevent lost updates** with one of ([references/concurrency-patterns.md](references/concurrency-patterns.md)):
   - a single atomic statement: `UPDATE ... SET qty = qty - 1 WHERE id = ? AND qty >= 1`, checking affected rows;
   - a conditional state transition: `UPDATE ... SET status = 'paid' WHERE id = ? AND status = 'pending'`;
   - optimistic locking with a `version` column, for low-contention edits;
   - `SELECT ... FOR UPDATE` inside a short transaction, on rows found by a unique key.
   Read, modify in application code, then save is never correct under concurrency without one of these.
10. **Claim work without contention** with `SELECT ... FOR UPDATE SKIP LOCKED` (PostgreSQL ≥ 9.5, MySQL ≥ 8.0.1) for queue-like tables, plus a reaper for claims that time out.
11. **Retry deadlocks and serialization failures** by re-running the **whole transaction** a bounded number of times with jitter. Under concurrency they are expected; not retrying them is the bug. Reduce frequency with consistent lock order, short transactions and precise indexes.
12. **Enforce uniqueness and idempotency with unique constraints**, treating the duplicate-key error as an expected outcome ("already done": read and return the existing row). Upsert syntax differs per engine; see the engine file.
13. **Keep transactions short and local.** Never hold one open across an HTTP call, a queue publish, or user think time. Side effects run after commit or through an outbox (`distributed-systems`).

### Topology

14. **Replicas lag the primary.** Read-after-write paths (show the order just placed, the decision just made) read from the primary, or tolerate staleness explicitly.
15. **Poolers change semantics.** In transaction-pooling mode, session state (`SET`, advisory locks held across statements, some prepared statement modes) doesn't survive between transactions. Check the mode before using session features.
16. **Failover** moves the primary; clients reconnect and retry only idempotent work.

## Output

Queries with the indexes that serve them and plan evidence; concurrency code using a named pattern with its retry policy; a note of every engine- or version-dependent feature used.

## Verification

- [ ] Plan output for each new or changed hot query, on realistic data, shows index use without full scans or sorts on large tables.
- [ ] List endpoints have a query-count assertion.
- [ ] Concurrent-update paths are covered by a test that runs two transactions or workers against the same row, on the real engine (not SQLite or an in-memory fake).
- [ ] Deadlock and serialization retries wrap whole transactions, bounded, with jitter.
- [ ] No transaction spans a network call.
- [ ] Read-after-write paths don't read from replicas.

## Escalation

Ask when: a fix needs a new index on a large hot table (migration plan and approval); isolation-level, collation or global settings changes are implied; a query needs an executing `EXPLAIN` against production; or replica lag affects a business guarantee.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's fast on my machine." | With 1,000 rows. `EXPLAIN` on realistic data, or it isn't verified. |
| "Collisions are rare." | Rare per request, certain at volume. Oversold stock and double-spent balances are incidents. |
| "The ORM handles concurrency." | It issues whatever reads and writes you wrote. Lost updates are a property of the pattern, not the library. |
| "A deadlock means a bug." | Under concurrency it is expected. Not retrying it is the bug. |

## References

- [references/concurrency-patterns.md](references/concurrency-patterns.md): conditional updates, optimistic locking, row locks, SKIP LOCKED, retry wrapper, uniqueness as idempotency.
- [references/postgresql.md](references/postgresql.md): read when the engine is PostgreSQL: MVCC, isolation, lock levels, plans, upserts, diagnostics.
- [references/mysql.md](references/mysql.md): read when the engine is MySQL or Aurora MySQL: InnoDB locking, collation and `sql_mode` traps, diagnostics.

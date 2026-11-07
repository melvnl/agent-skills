---
name: mysql-engineering
description: Applies MySQL/InnoDB and Aurora behavior correctly: index design verified with EXPLAIN, isolation levels and locking reads, deadlock and lock-timeout retries, optimistic and row locking for concurrent updates, collation and type-conversion traps, keyset pagination, batched writes, and Aurora reader lag and failover. Use when writing or tuning MySQL queries, handling concurrency, or diagnosing slow queries, deadlocks or lock waits.
---

# MySQL Engineering

## Overview

MySQL behaves differently from the defaults many developers assume: REPEATABLE READ with gap locks, case-insensitive comparisons, implicit DDL commits, no cached row count, and replicas that lag. Queries that pass tests on small data time out at volume, and concurrent updates silently lose writes. This skill applies InnoDB's real behavior to query design and concurrency, and verifies plans with `EXPLAIN` rather than intuition.

## When to use

- Writing or optimizing queries and indexes on MySQL or Aurora MySQL.
- Implementing concurrent updates, counters, job claiming, uniqueness, or idempotency in the database.
- Diagnosing slow queries, deadlocks (error 1213), lock wait timeouts (1205), or replica lag.

**When not to use:** engine-agnostic modeling → `database-design`. Rolling out schema changes → `database-migrations`.

## Inputs and context

1. **Engine and version**: MySQL 5.7 vs 8.0 (point release matters: `SKIP LOCKED`/`NOWAIT` 8.0.1, `EXPLAIN ANALYZE` 8.0.18, `CHECK` enforced 8.0.16), or Aurora MySQL version.
2. Session and server settings that change behavior: transaction isolation, `sql_mode`, default charset and collation, `innodb_lock_wait_timeout`, `wait_timeout`.
3. The table's definition (`SHOW CREATE TABLE`), indexes, and approximate size.
4. The actual query, as executed (ORM-generated SQL captured from logs or `str(queryset.query)`), with realistic parameters.
5. Topology: writer and reader endpoints, connection pooling, how the app routes reads.

## Process

### Queries and indexes

1. **Get the real SQL** and run `EXPLAIN` (and `EXPLAIN ANALYZE` on 8.0.18+, on a non-production copy if it executes the query). Look at `type` (avoid `ALL` on large tables), `key`, `rows`, and `Extra` (`Using filesort`, `Using temporary`).
2. **Design composite indexes for the query**: equality predicates first, then one range or the `ORDER BY` columns; the leftmost prefix must match. InnoDB secondary indexes include the primary key, which enables covering reads.
3. **Avoid index killers**: functions on indexed columns (`DATE(created_at) = ...` → range on `created_at`); implicit type conversion (comparing a `VARCHAR` column with a number scans the table); leading wildcards (`LIKE '%x'`); `OR` across different columns (consider `UNION`).
4. **Paginate with keysets** (`WHERE (created_at, id) > (?, ?) ORDER BY created_at, id LIMIT 50`), not large `OFFSET`s, which scan and discard every skipped row.
5. **Don't count what you don't need.** InnoDB has no cached row count; `COUNT(*)` on a large table scans an index. Use `EXISTS` for presence; maintain counters or approximate counts for dashboards.
6. **Batch large writes and deletes** by primary-key ranges with small transactions; a single huge `DELETE` or `UPDATE` holds locks, grows the undo log, and lags replicas.

### Concurrency

7. **Know the isolation level.** InnoDB defaults to REPEATABLE READ: consistent snapshot reads, and *locking* reads and writes take next-key (gap) locks on scanned ranges, which is a frequent cause of unexpected blocking and deadlocks. Some systems run READ COMMITTED; check the session.
8. **Prevent lost updates** with one of ([references/mysql-concurrency.md](references/mysql-concurrency.md)):
   - a single atomic `UPDATE ... SET n = n + 1` or a conditional `UPDATE ... WHERE status = 'pending'` checking affected rows;
   - optimistic locking with a `version` column;
   - `SELECT ... FOR UPDATE` inside a short transaction on rows found by a **unique index** (ranges lock gaps).
9. **Claim work without contention** with `SELECT ... FOR UPDATE SKIP LOCKED` (8.0.1+) for queue-like tables.
10. **Retry deadlocks and lock-wait timeouts** by re-running the **whole transaction** a bounded number of times with jitter. Deadlocks are normal under concurrency; their frequency is reduced by consistent lock ordering, short transactions, and precise indexes.
11. **Enforce uniqueness and idempotency with unique keys**, handling the duplicate-key error (1062) as an expected outcome. Be careful with `INSERT IGNORE`, which also downgrades other errors (e.g. truncation) to warnings.
12. **Keep transactions short**, and never hold one open across network calls (HTTP, queue publishes). Long transactions block purge (growing the history list) and hold locks.

### Correctness traps

13. **Collation**: the 8.0 default `utf8mb4_0900_ai_ci` is case- and accent-insensitive, so `'A' = 'a'` and unique keys treat them as duplicates. Use a binary or `_cs` collation where exact matching matters (tokens, codes). `utf8` means the 3-byte `utf8mb3`; use `utf8mb4`.
14. **`sql_mode`**: without strict mode, invalid values are truncated with a warning instead of an error. Check before relying on the database to reject bad data.
15. **Time**: `TIMESTAMP` converts through the session time zone and ends in 2038; `DATETIME` stores what you give it. Write UTC consistently.

### Aurora

16. **Reader endpoints lag the writer** (usually milliseconds, more under load). Read-after-write paths (show the decision just made) read from the writer, or tolerate staleness explicitly.
17. **Failover** changes the writer behind the cluster endpoint; clients must reconnect and retry idempotent work. Keep DNS caching short and pool connections validated.

## Output

Queries with the indexes that serve them and `EXPLAIN` evidence; concurrency code using the chosen pattern with its retry policy; a note of version-dependent features.

## Verification

- [ ] `EXPLAIN` output for each new or changed hot query, on realistic data, shows index use without full scans or filesorts on large tables.
- [ ] Concurrent-update paths are covered by a test that runs two transactions or workers against the same row (on MySQL, not SQLite).
- [ ] Deadlock and lock-timeout retries wrap whole transactions, bounded, with jitter.
- [ ] No transaction spans a network call.
- [ ] Collation and `sql_mode` assumptions were checked for comparisons and uniqueness that matter.
- [ ] Read-after-write paths don't read from replicas.

## Escalation

Ask when: a fix needs a new index on a large hot table (migration plan and approval); isolation-level or `sql_mode` changes are implied (global behavior); queries need production `EXPLAIN ANALYZE` (it executes the query); or replica lag affects a business guarantee.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's fast on my machine." | With 1,000 rows. `EXPLAIN` on realistic data, or it isn't verified. |
| "Read, modify, save is fine; collisions are rare." | Rare per request, certain at volume. Lost updates in money or decisions are incidents. |
| "Deadlock means a bug." | Under concurrency, deadlocks are expected. Not retrying them is the bug. |

## References

- [references/mysql-concurrency.md](references/mysql-concurrency.md): conditional updates, optimistic locking, FOR UPDATE, SKIP LOCKED, retry wrapper, duplicate-key handling.

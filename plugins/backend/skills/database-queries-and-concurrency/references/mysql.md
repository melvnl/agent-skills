# MySQL / InnoDB / Aurora MySQL notes

Point releases matter: `SKIP LOCKED`/`NOWAIT` 8.0.1, `CHECK` enforced 8.0.16, `EXPLAIN ANALYZE` 8.0.18. Check `SELECT VERSION();`.

## Isolation and locks

- Default isolation is **REPEATABLE READ**: plain reads use a consistent snapshot; *locking* reads and writes take next-key (gap) locks on the ranges they scan. Gap locks are the usual cause of unexpected blocking and deadlocks on inserts. Some systems run READ COMMITTED; check `@@transaction_isolation`.
- Lock rows by unique-index lookup to lock one row; a range or non-unique predicate locks gaps too.
- `FOR SHARE` (8.0; `LOCK IN SHARE MODE` before) blocks writers but not readers.
- `innodb_lock_wait_timeout` (default 50 s) is usually far too long for request paths; set it per session.

## Retryable errors

`1213` deadlock, `1205` lock wait timeout. Duplicate key: `1062`.

## Plans

- `EXPLAIN`: watch `type` (`ALL` = full scan), `key`, `rows`, and `Extra` (`Using filesort`, `Using temporary`).
- InnoDB secondary indexes include the primary key, which enables covering reads.
- InnoDB has no cached row count; `COUNT(*)` scans an index.

## Correctness traps

- **Collation**: the 8.0 default `utf8mb4_0900_ai_ci` is case- and accent-insensitive: `'A' = 'a'`, and unique keys treat them as duplicates. Use a binary or `_cs` collation for tokens and codes. `utf8` is the 3-byte `utf8mb3`; use `utf8mb4`.
- **`sql_mode`**: without strict mode, invalid values are truncated with a warning instead of rejected.
- **Time**: `TIMESTAMP` converts through the session time zone and ends in 2038; `DATETIME(6)` stores what you give it. Write UTC consistently.
- **DDL commits implicitly**: a multi-statement migration is not atomic (`database-migrations`).
- `INSERT IGNORE` also downgrades other errors (truncation) to warnings. `INSERT ... ON DUPLICATE KEY UPDATE` reports 1 affected row for insert, 2 for update, and may consume auto-increment values.

## Aurora

- Reader endpoints lag the writer (usually milliseconds, more under load).
- Failover changes the writer behind the cluster endpoint; keep DNS caching short and validate pooled connections.

## Diagnostics

- Latest deadlock: `SHOW ENGINE INNODB STATUS\G` (LATEST DETECTED DEADLOCK).
- Lock waits: `performance_schema.data_lock_waits` joined with `data_locks` (8.0); `information_schema.innodb_lock_waits` (5.7).
- Long transactions: `SELECT * FROM information_schema.innodb_trx ORDER BY trx_started LIMIT 10;`

# PostgreSQL notes

Check the server version (`SELECT version();`) before using anything marked with one.

## MVCC and isolation

- Default isolation is **READ COMMITTED**: each statement sees data committed before it started. Two statements in one transaction can see different data.
- A blocked `UPDATE ... WHERE` re-evaluates its `WHERE` against the newly committed row version after the lock is released. That is why the atomic and conditional update patterns are safe here.
- `REPEATABLE READ` and `SERIALIZABLE` raise serialization failures (`40001`) instead of blocking; callers must retry the whole transaction.
- Updates write new row versions; dead tuples are reclaimed by (auto)vacuum. Long-running transactions, including idle-in-transaction sessions, stop vacuum from cleaning up and bloat tables. Set `idle_in_transaction_session_timeout`.

## Locks

- Row locks: `FOR UPDATE` (blocks other writers and lockers), `FOR NO KEY UPDATE` (what plain `UPDATE` takes unless keys change), `FOR SHARE`, `FOR KEY SHARE`. Foreign key checks take `FOR KEY SHARE` on the parent row.
- `NOWAIT` fails immediately; `SKIP LOCKED` (≥ 9.5) skips locked rows.
- Advisory locks (`pg_advisory_xact_lock(key)`) coordinate application-level critical sections; the `_xact_` form releases at transaction end and is safe with transaction-mode poolers. Session-level advisory locks are not.
- Set `lock_timeout` and `statement_timeout` per session or role so a stuck query fails instead of piling up.

## Retryable errors

`40P01` deadlock_detected, `40001` serialization_failure, `55P03` lock_not_available (from `NOWAIT` or `lock_timeout`). Duplicate key: `23505` unique_violation.

## Plans

- `EXPLAIN (ANALYZE, BUFFERS)` executes the query; run it on a copy or inside a transaction you roll back (that still performs writes until rollback).
- Watch for `Seq Scan` on large tables, `Sort` spilling to disk, nested loops with large outer row counts, and estimated vs actual rows far apart (stale stats: `ANALYZE table`).
- Index types: B-tree (default), GIN for `jsonb` containment, arrays and full-text, partial indexes (`WHERE deleted_at IS NULL`) for "active rows" rules, expression indexes (`lower(email)`).
- `pg_stat_statements` ranks queries by total time; start there for "the database is slow".

## Upserts

`INSERT ... ON CONFLICT (cols) DO NOTHING` / `DO UPDATE SET ...`. `RETURNING` returns nothing for `DO NOTHING` on conflict; select the existing row afterwards. Sequences advance even when the insert doesn't happen.

## Types

- `timestamptz` for instants (stored as UTC); plain `timestamp` drops the zone.
- `numeric(p, s)` for money; never `real`/`double precision`. The `money` type depends on locale settings; avoid it.
- `text` with a `CHECK` is usually better than a native `ENUM`, whose values can be added but not removed or reordered easily.

## Diagnostics

- Blocking: `SELECT pid, pg_blocking_pids(pid), state, wait_event_type, query FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;`
- Long transactions: `SELECT pid, now() - xact_start AS age, state, query FROM pg_stat_activity WHERE xact_start IS NOT NULL ORDER BY age DESC LIMIT 10;`
- Deadlock details appear in the server log.

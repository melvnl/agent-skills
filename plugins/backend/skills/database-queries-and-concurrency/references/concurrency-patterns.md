# Concurrency patterns

Engine-neutral SQL. Engine-specific syntax and error codes are in `postgresql.md` and `mysql.md`.

## Atomic update (counters, stock, balances)

```sql
UPDATE inventory_level SET reserved = reserved + :qty
WHERE id = :id AND stocked - reserved >= :qty;
-- 1 row: reserved; 0 rows: insufficient stock -> reject, don't retry blindly
```

The check and the change happen in one statement, so no other writer can interleave.

## Conditional state transition

```sql
UPDATE payment SET status = 'captured', captured_at = :now
WHERE id = :id AND status = 'authorized';
-- 1 row: transition happened; 0 rows: someone else moved it first -> 409 or no-op
```

ORMs expose the affected-row count (Django `.filter(...).update(...)`, SQLAlchemy `result.rowcount`, MikroORM `nativeUpdate` return value, Prisma `updateMany().count`). Use it; don't read-then-save.

## Optimistic locking

```sql
UPDATE product SET title = :title, version = version + 1
WHERE id = :id AND version = :read_version;
-- 0 rows: stale read; reload and retry, or report a conflict to the user
```

Fits low-contention edits (admin forms, profile updates). Under high contention, conflicts pile up; use an atomic update or a row lock.

## Row lock for read-modify-write

```sql
BEGIN;
SELECT balance FROM wallet WHERE id = :id FOR UPDATE;   -- lookup by unique key locks one row
-- compute in application code
UPDATE wallet SET balance = :new_balance WHERE id = :id;
COMMIT;
```

Rules: lock by unique key (range predicates lock more than you think, especially on InnoDB); lock rows in a consistent order (ascending id) across all code paths; keep the transaction short; no network calls inside.

## Job claiming

```sql
BEGIN;
SELECT id FROM job WHERE status = 'queued' ORDER BY id LIMIT 10 FOR UPDATE SKIP LOCKED;
UPDATE job SET status = 'running', claimed_by = :worker, claimed_at = :now WHERE id IN (...);
COMMIT;
```

PostgreSQL ≥ 9.5, MySQL ≥ 8.0.1. Add a reaper that requeues `running` jobs past a timeout.

## Retry wrapper

Retry the **whole** unit of work, only when it is safe to repeat (no external side effects inside the transaction), bounded, with jittered backoff. Log retries at WARNING with the attempt number.

```python
def run_with_retry(fn, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            with transaction():          # the project's transaction helper
                return fn()
        except RetryableDbError:         # deadlock / serialization failure / lock timeout, per engine file
            if attempt == attempts:
                raise
            sleep((2 ** attempt) * 0.05 + random.uniform(0, 0.05))
```

```ts
async function runWithRetry<T>(fn: (tx: Tx) => Promise<T>, attempts = 3): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await db.transaction(fn);   // the project's transaction helper
    } catch (err) {
      if (!isRetryableDbError(err) || attempt >= attempts) throw err;
      await sleep(2 ** attempt * 50 + Math.random() * 50);
    }
  }
}
```

## Uniqueness as idempotency

```sql
CREATE UNIQUE INDEX uq_payment_attempt ON payment_attempt (order_id, idempotency_key);
```

Insert; on the duplicate-key error, read and return the existing row. Upsert syntax differs per engine (see the engine file); know what the statement returns on insert vs update.

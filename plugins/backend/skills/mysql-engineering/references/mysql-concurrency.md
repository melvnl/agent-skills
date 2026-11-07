# MySQL concurrency patterns

## Conditional update (state transition)

```sql
UPDATE application SET status = 'approved', decided_at = UTC_TIMESTAMP(6)
WHERE id = ? AND status = 'pending';
-- affected rows = 1: transition happened; 0: someone else moved it first -> 409
```

Django: `Application.objects.filter(pk=pk, status="pending").update(status="approved")` returns the affected count.

## Optimistic locking

```sql
UPDATE application SET limit_amount = ?, version = version + 1
WHERE id = ? AND version = ?;
-- 0 rows: stale read; reload and retry or report a conflict
```

Fits low-contention edits (admin changes, profile updates). Under high contention, conflicts and retries pile up; use row locks or atomic updates instead.

## Row lock for read-modify-write

```sql
START TRANSACTION;
SELECT balance_cents FROM wallet WHERE id = ? FOR UPDATE;   -- unique-index lookup locks one row
-- compute in application
UPDATE wallet SET balance_cents = ? WHERE id = ?;
COMMIT;
```

Rules: lock by unique key (a range predicate takes gap locks and blocks inserts into the range); lock rows in a consistent order (e.g. ascending id) across code paths; keep the transaction short; no network calls inside.

`FOR SHARE` (8.0; `LOCK IN SHARE MODE` before) for reads that must block concurrent writers but not other readers.

## Job claiming

```sql
START TRANSACTION;
SELECT id FROM score_refresh_job
WHERE status = 'queued' ORDER BY id LIMIT 10
FOR UPDATE SKIP LOCKED;
UPDATE score_refresh_job SET status = 'running', claimed_by = ?, claimed_at = UTC_TIMESTAMP(6) WHERE id IN (...);
COMMIT;
```

Requires MySQL 8.0.1+ (not 5.7). Add a reaper for jobs stuck in `running` past a timeout.

## Retry wrapper

```python
import random
import time

from django.db import OperationalError, transaction

RETRYABLE = {1213, 1205}   # deadlock, lock wait timeout

def run_with_retry(fn, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            with transaction.atomic():
                return fn()
        except OperationalError as exc:
            code = exc.args[0] if exc.args else None
            if code not in RETRYABLE or attempt == attempts:
                raise
            time.sleep((2 ** attempt) * 0.05 + random.uniform(0, 0.05))
```

Retry the **whole** unit of work, and only work that is safe to repeat (no external side effects inside, `on_commit` for those). Log retries at WARNING with `retry_count`.

## Uniqueness as idempotency

```sql
CREATE UNIQUE INDEX uq_decision_request ON decision (application_id, request_key);
```

Insert, and treat duplicate-key error 1062 as "already done": read and return the existing row. `INSERT ... ON DUPLICATE KEY UPDATE` is an upsert; note that `LAST_INSERT_ID()` and affected-row semantics differ for inserts vs updates (1 vs 2 affected rows), and auto-increment values may be consumed.

## Diagnosing

- Latest deadlock: `SHOW ENGINE INNODB STATUS\G` (section LATEST DETECTED DEADLOCK).
- Current lock waits (8.0): `performance_schema.data_lock_waits` joined with `data_locks`; 5.7: `information_schema.innodb_lock_waits`.
- Long transactions: `SELECT * FROM information_schema.innodb_trx ORDER BY trx_started LIMIT 10;`

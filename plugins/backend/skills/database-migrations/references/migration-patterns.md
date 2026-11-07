# Migration patterns

## Change types

| Change | Safe pattern |
|---|---|
| Add table | single step |
| Add nullable column | single step; MySQL 8.0 can often do it `INSTANT` (8.0.12+ at the end of the table; 8.0.29+ any position), subject to limitations: check `ALGORITHM=INSTANT` succeeds instead of assuming |
| Add column with `NOT NULL` | add nullable (or with a default) → backfill → enforce `NOT NULL` (table rebuild on many versions: rehearse) |
| Add index | online (`ALGORITHM=INPLACE, LOCK=NONE`) or online schema change tool; build time scales with table size |
| Add unique constraint | first find and resolve duplicates (query + owner decision), then add; failing midway on duplicates wastes the build |
| Add foreign key | ensure orphans are cleaned first; FK checks add write cost; follow the project's FK policy |
| Rename column / table | expand-contract: add new → dual-write → backfill → switch reads → stop writing old → drop old later |
| Change type | as rename: new column of the new type, backfill with conversion, switch, drop old |
| Drop column | remove all code references → deploy → drop in a later migration. In Django, removing the field from the model *and* dropping in the same deploy breaks running old code |
| Drop table | stop all access, keep a backup or snapshot, drop after a grace period |
| Data fix | idempotent batch job with dry-run mode and a report of affected rows |

## MySQL / Aurora DDL notes

- Check the algorithm explicitly: `ALTER TABLE t ADD COLUMN c INT NULL, ALGORITHM=INSTANT;` fails fast if it can't be instant, instead of silently rebuilding.
- Online DDL still takes a brief exclusive metadata lock at start and end. A long-running transaction or open read on the table blocks it, and every new query queues behind the waiting DDL. Before running: check for long transactions (`information_schema.innodb_trx`), and set `lock_wait_timeout` low for the DDL session so it gives up instead of stalling traffic.
- Large rebuilds generate replication or Aurora replica lag; schedule and monitor.
- `gh-ost` / `pt-online-schema-change` copy into a shadow table and swap; they need sufficient disk and have their own trigger or binlog requirements. Use what the team already operates.

## Django specifics

- `python manage.py sqlmigrate app 0042` shows the SQL; `python manage.py migrate --plan` shows what would run.
- `makemigrations` asks about renames interactively; in non-interactive generation it may produce `RemoveField` + `AddField` (data loss). Read the file.
- `RunPython(forward, reverse)`; use `apps.get_model(...)` inside it, never imported models (they reflect current code, not the historical state).
- Mark data migrations `atomic = False` when they batch commits themselves; on MySQL schema operations aren't transactional anyway.
- `SeparateDatabaseAndState` lets model state and database operations diverge for multi-step rollouts.

## Backfill template

```python
BATCH = 5000

def backfill(dry_run=True, start_after=0, sleep_s=0.2):
    last_id = start_after
    while True:
        ids = list(
            Application.objects.filter(id__gt=last_id, decision_reason__isnull=True, status__in=DECIDED)
            .order_by("id").values_list("id", flat=True)[:BATCH]
        )
        if not ids:
            break
        if not dry_run:
            with transaction.atomic():
                (Application.objects.filter(id__in=ids, decision_reason__isnull=True)
                 .update(decision_reason=derive_reason_sql()))
        last_id = ids[-1]
        logger.info("backfill_batch_completed", extra={"last_id": last_id, "batch_size": len(ids), "dry_run": dry_run})
        time.sleep(sleep_s)
```

Properties: keyset pagination by id (no OFFSET), re-check of the condition inside the update (idempotent), resumable from `last_id`, throttled, observable, dry run by default.

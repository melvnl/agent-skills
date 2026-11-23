# Migration patterns

## Change types

| Change | Safe pattern |
|---|---|
| Add table | single step |
| Add nullable column | single step; usually metadata-only (check the engine notes for your version) |
| Add column with `NOT NULL` | add nullable (or with a constant default) → backfill → enforce `NOT NULL` (on PostgreSQL via a validated `CHECK` first, to avoid a long exclusive scan) |
| Add index | the engine's online path (`CREATE INDEX CONCURRENTLY`, `ALGORITHM=INPLACE, LOCK=NONE`) or an online schema change tool; build time scales with table size |
| Add unique constraint | find and resolve duplicates first (query + owner decision), then build the unique index online and attach it |
| Add foreign key | clean orphans first; on PostgreSQL add `NOT VALID`, then `VALIDATE CONSTRAINT` separately |
| Rename column / table | expand-contract: add new → dual-write → backfill → switch reads → stop writing old → drop old later |
| Change type | as rename: new column of the new type, backfill with conversion, switch, drop old |
| Drop column | remove all code references (including ORM model fields that would still select it) → deploy → drop in a later migration |
| Drop table | stop all access, keep a backup or snapshot, drop after a grace period |
| Data fix | idempotent batch job with dry-run mode and a report of affected rows |

## Backfill template

The same shape in any language: keyset pagination by id, the condition re-checked inside the update, resumable from the last id, throttled, observable, dry run by default.

```sql
-- one batch; :last_id starts at 0 and advances to the max id returned
UPDATE "order" SET fulfillment_status = derive_status(...)
WHERE id IN (
  SELECT id FROM "order"
  WHERE id > :last_id AND fulfillment_status IS NULL
  ORDER BY id LIMIT 5000
)
AND fulfillment_status IS NULL
RETURNING id;
```

```ts
async function backfill({ dryRun = true, startAfter = "", sleepMs = 200 } = {}) {
  let lastId = startAfter;
  for (;;) {
    const ids = await selectIds({ after: lastId, where: "fulfillment_status IS NULL", limit: 5000 });
    if (ids.length === 0) break;
    if (!dryRun) await updateBatch(ids);           // re-checks the condition; own short transaction
    lastId = ids[ids.length - 1];
    logger.info("backfill_batch_completed", { lastId, batchSize: ids.length, dryRun });
    await sleep(sleepMs);
  }
}
```

Run it as a job or script, not inside the schema migration, so a failure resumes from `lastId` instead of rolling back hours of work.

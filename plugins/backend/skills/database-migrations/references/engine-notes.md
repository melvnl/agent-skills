# Engine notes for migrations

## PostgreSQL

- **DDL is transactional**: a failed migration rolls back cleanly, except statements that can't run in a transaction (`CREATE INDEX CONCURRENTLY`, `DROP INDEX CONCURRENTLY`, `ALTER TYPE ... ADD VALUE` before 12). Migration tools need a "no transaction" flag for those.
- **Every `ALTER TABLE` takes an `ACCESS EXCLUSIVE` lock**, however briefly. It queues behind any running transaction on the table, and all later queries queue behind it. Always `SET lock_timeout = '3s'` (or similar) in the migration session and retry on timeout, rather than stalling production.
- Metadata-only (fast): adding a nullable column; adding a column with a constant default (11+); dropping a column; `SET DEFAULT`.
- Rewrites or full scans (slow under lock): changing a column type (except some binary-compatible changes such as widening `varchar`); adding a column with a volatile default (`now()`, `gen_random_uuid()`); `SET NOT NULL` (scans, unless a validated `CHECK (col IS NOT NULL)` exists, 12+).
- **Indexes**: `CREATE INDEX CONCURRENTLY` doesn't block writes, takes longer, and on failure leaves an `INVALID` index to drop and retry. Build unique indexes concurrently, then `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX`.
- **Constraints**: add `CHECK` and foreign keys as `NOT VALID` (brief lock, enforced for new rows), then `VALIDATE CONSTRAINT` (scans with a weaker lock).
- Enums: adding a value is cheap; removing or renaming values isn't. Prefer `text` + `CHECK` for sets that change.
- Before running: check long transactions in `pg_stat_activity` (`xact_start`), and run on a replica-lag-aware schedule for large rewrites.

## MySQL / Aurora MySQL

- **DDL commits implicitly**: a migration with several operations is not atomic and can be left half-applied. One risky operation per migration.
- State the algorithm explicitly so it fails fast instead of silently rebuilding: `ALTER TABLE t ADD COLUMN c INT NULL, ALGORITHM=INSTANT;` (8.0.12+ at the end of the table, 8.0.29+ any position, with limitations), `ALGORITHM=INPLACE, LOCK=NONE` for most index builds.
- Online DDL still takes a brief exclusive metadata lock at start and end. A long transaction or open read blocks it, and new queries queue behind it. Check `information_schema.innodb_trx` first and set `lock_wait_timeout` low for the DDL session.
- Large rebuilds lag replicas and Aurora readers; schedule and monitor.
- `gh-ost` / `pt-online-schema-change` copy into a shadow table and swap; they need disk headroom and have trigger or binlog requirements. Use what the team operates.
- `CHECK` constraints are enforced only from 8.0.16; earlier versions parse and ignore them.

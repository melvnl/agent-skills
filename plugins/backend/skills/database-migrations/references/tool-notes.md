# Migration tool notes

Read the section for the tool the project uses. Check its version first; flags change between releases.

## Django

- `python manage.py sqlmigrate <app> <migration>` shows the SQL; `migrate --plan` shows what would run.
- `makemigrations` may produce `RemoveField` + `AddField` for a rename (data loss). Read the file.
- `RunPython(forward, reverse)`; inside it use `apps.get_model(...)`, never imported models (they reflect current code, not historical state). `RunPython.noop` with a comment when irreversible.
- `atomic = False` for migrations that must run outside a transaction (concurrent index builds; batched data migrations). Django ≥ 3.0 has `AddIndexConcurrently` in `django.contrib.postgres.operations`.
- `SeparateDatabaseAndState` lets model state and database operations diverge for multi-step rollouts.

## Alembic (SQLAlchemy)

- `alembic upgrade head --sql` renders SQL offline for review.
- Autogenerate misses or misreads renames, server defaults and some type changes; edit the generated script.
- Concurrent index builds: `with op.get_context().autocommit_block(): op.create_index(..., postgresql_concurrently=True)`.

## MikroORM (Medusa v2 modules)

- Medusa generates module migrations from data models: `npx medusa db:generate <module_name>`; apply with `npx medusa db:migrate` (which also syncs module links). Read the generated class in `src/modules/<module>/migrations/` before applying.
- Generated `up()` is raw SQL strings: you can split risky statements into separate migrations or replace them with concurrent/`NOT VALID` forms. A statement that can't run in a transaction needs its own migration with transactions disabled for it; check how the installed MikroORM version exposes that.
- Link tables are managed by `db:migrate` / `db:sync-links`; removing a link definition can drop its table. Review the sync output.
- Never edit core Medusa module migrations; extend with your own module or link.

## Prisma

- `prisma migrate dev --create-only` creates the SQL without applying it; edit it before `migrate deploy`.
- Prisma detects renames as drop + add; rewrite as `ALTER TABLE ... RENAME COLUMN` or expand-contract.
- `migrate deploy` runs each migration in a transaction on PostgreSQL; concurrent index builds need a separate migration file containing only that statement (check your Prisma version's support).

## TypeORM

- `migration:generate` diffs entities against the database; review renames and drops. Set `transaction = false` on a migration class for concurrent index builds.
- Never enable `synchronize: true` outside local development; it alters production schemas without review.

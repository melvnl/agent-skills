# melvin-backend

Python backend engineering for services that run on Django or FastAPI, MySQL/Aurora, Redis, and AWS SQS/SNS. Every skill starts by detecting the project's actual versions and conventions; none assumes modern features in a legacy codebase.

Depends on `melvin-engineering` and `melvin-observability` (installed automatically).

## Skills

- **[python-backend-engineering](skills/python-backend-engineering/SKILL.md)**: Version-safe Python backend code: typed boundaries, explicit timeouts, aware datetimes, Decimal money, exception chaining, pure domain logic.
- **[django-engineering](skills/django-engineering/SKILL.md)**: Version-correct Django/DRF: service-layer rules, constraints, efficient querysets, transactions with on_commit side effects, safe bulk ops, explicit permissions.
- **[fastapi-engineering](skills/fastapi-engineering/SKILL.md)**: Version-correct FastAPI/Pydantic: sync vs async endpoints, auth and session dependencies, leak-proof response models, safe errors, lifespan, durable work on queues.
- **[api-design](skills/api-design/SKILL.md)**: HTTP contracts: status semantics, a stable error model, idempotency keys, pagination, money and time formats, compatible evolution, contract tests.
- **[database-design](skills/database-design/SKILL.md)**: Schemas from the domain: ownership, keys, database-enforced invariants, history snapshots, exact money and UTC time, query-derived indexes.
- **[database-migrations](skills/database-migrations/SKILL.md)**: Deploy-compatible migrations: expand-migrate-contract, non-blocking DDL on large MySQL tables, resumable backfills, generated-SQL review, rehearsal and rollback plans.
- **[mysql-engineering](skills/mysql-engineering/SKILL.md)**: InnoDB and Aurora done right: EXPLAIN-verified indexes, isolation and locking reads, deadlock retries, lost-update prevention, collation traps, replica lag.
- **[redis-engineering](skills/redis-engineering/SKILL.md)**: Redis for derivable, expirable data: TTL'd cache-aside, post-commit invalidation, stampede protection, atomic ops, token-checked locks, graceful degradation.
- **[distributed-systems](skills/distributed-systems/SKILL.md)**: Partial-failure-safe interactions: timeouts, bounded jittered retries, unknown-outcome handling, idempotent consumers, outbox not dual writes, sagas, breakers, parity migrations.
- **[async-messaging](skills/async-messaging/SKILL.md)**: Reliable SQS/SNS: standard vs FIFO, versioned envelopes, idempotent consumers, visibility timeouts, delete-after-success, DLQs, compatible schema evolution.
- **[performance-engineering](skills/performance-engineering/SKILL.md)**: Measurement-driven performance: a percentile target, realistic reproduction, profiling to the real bottleneck, highest-leverage fix, same-conditions before/after.

## Agents

- **[backend-engineer](agents/backend-engineer.md)**: Implements one approved task at a time test-first, instrumented, within scope; reports verified results; never approves its own work.

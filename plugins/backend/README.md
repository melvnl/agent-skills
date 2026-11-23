# backend-engineering

Stack-agnostic backend and web engineering. The skills describe methods that hold in any language, framework, engine or broker; engine-, tool- and broker-specific details (PostgreSQL, MySQL, Django, MikroORM, Prisma, SQS, Kafka, BullMQ, Next.js and others) live in each skill's `references/` and are read only when the project uses them. Every skill starts by detecting the project's actual versions and conventions.

Depends on `spec-driven-engineering` and `observability` (installed automatically).

## Skills

- **[api-design](skills/api-design/SKILL.md)**: HTTP contracts: status semantics, a stable error model, idempotency keys, pagination, money and time formats, compatible evolution, contract tests.
- **[database-design](skills/database-design/SKILL.md)**: Schemas from the domain: ownership, keys, database-enforced invariants, history snapshots, exact money and UTC time, query-derived indexes.
- **[database-migrations](skills/database-migrations/SKILL.md)**: Deploy-compatible migrations on any engine and tool: expand-migrate-contract, non-blocking DDL, resumable backfills, generated-SQL review, rehearsal and rollback plans.
- **[database-queries-and-concurrency](skills/database-queries-and-concurrency/SKILL.md)**: EXPLAIN-verified queries and indexes, keyset pagination, lost-update prevention, locking reads, SKIP LOCKED, deadlock retries, replica lag; PostgreSQL and MySQL notes.
- **[caching-and-coordination](skills/caching-and-coordination/SKILL.md)**: Caches, rate limits and locks on any store: TTL'd cache-aside, post-commit invalidation, stampede protection, complete keys, token-checked locks, graceful degradation.
- **[distributed-systems](skills/distributed-systems/SKILL.md)**: Partial-failure-safe interactions: timeouts, bounded jittered retries, unknown-outcome handling, idempotent consumers, outbox not dual writes, sagas, breakers, parity migrations.
- **[async-messaging](skills/async-messaging/SKILL.md)**: Reliable messaging on any broker or job queue: delivery guarantees, envelopes, idempotent consumers, ack-after-success, redelivery timeouts, dead letters, compatible schema evolution.
- **[performance-engineering](skills/performance-engineering/SKILL.md)**: Measurement-driven performance for services and pages: percentile and Core Web Vitals targets, profiling to the real bottleneck, highest-leverage fix, same-conditions before/after.

## Agents

- **[backend-engineer](agents/backend-engineer.md)**: Implements one approved task at a time test-first, instrumented, within scope; reports verified results; never approves its own work.
- **[database-engineer](agents/database-engineer.md)**: Schema changes, deploy-compatible migrations, resumable backfills and EXPLAIN-verified queries with rehearsal evidence; never touches production.

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

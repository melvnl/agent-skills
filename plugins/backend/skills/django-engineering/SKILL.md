---
name: django-engineering
description: Builds and changes Django and Django REST Framework code that matches the project's Django version: models and constraints, efficient querysets, correct transaction boundaries with on_commit side effects, safe bulk operations, DRF validation and permissions, settings and security. Use when working in a Django project: models, views, serializers, admin, signals, management commands, Celery tasks.
---

# Django Engineering

## Overview

Django makes the common case easy and some costly mistakes silent: N+1 queries, side effects that fire for rolled-back transactions, bulk operations that skip business logic, permissions left at their defaults. This skill keeps Django work version-correct and puts business rules, transactions, and queries where they behave predictably.

## When to use

- Changing models, querysets, views, DRF serializers or viewsets, admin, signals, management commands, or Celery tasks in a Django project.
- Reviewing Django code for performance, transactional, or security issues.

**When not to use:** writing the migration file and its rollout → `database-migrations`. MySQL engine behavior (locking, indexes, isolation) → `mysql-engineering`. General Python → `python-backend-engineering`.

## Inputs and context

1. **Versions**: Django and DRF from the lockfile or `requirements*.txt`; Python version; database engine and version. Check every feature below against them ([references/django-version-notes.md](references/django-version-notes.md)).
2. **Settings layout**: split settings, environment loading, `DATABASES` (including `ATOMIC_REQUESTS` and `CONN_MAX_AGE`), `USE_TZ`, `TIME_ZONE`, `LOGGING`, DRF defaults (`DEFAULT_PERMISSION_CLASSES`, pagination, throttling).
3. **Project conventions**: where business logic lives (services/domain modules vs fat models vs views), how apps are split, how tests are written.
4. Existing patterns for background work (Celery, management commands, cron) and events (signals vs explicit calls).

## Process

1. **Put business rules in a service or domain layer**, not in views, serializers, signals, or `save()` overrides. Views and serializers parse, validate, call the service, and map the result. This keeps rules testable and callable from tasks and commands.
2. **Model the data deliberately.** `DecimalField` for money; `null=True` on string fields only with a reason (Django convention: empty string for "no value"); database-level invariants with `Meta.constraints` (`UniqueConstraint`, `CheckConstraint`) rather than only Python validation; indexes for real query patterns (`database-design`).
3. **Query efficiently.** Use `select_related` (FK/one-to-one) and `prefetch_related` (reverse/many-to-many) for related access in loops; `.exists()` instead of `len()` or `count()` for presence; `.only()`/`.values()` for wide tables; `.iterator(chunk_size=...)` for large scans. Pin query counts in tests for list endpoints ([references/django-orm-pitfalls.md](references/django-orm-pitfalls.md)).
4. **Get transaction boundaries right.**
   - Group writes that must succeed together in `transaction.atomic()`.
   - Trigger side effects (publishing to SQS/SNS, sending SMS, calling another service, enqueueing Celery tasks) with `transaction.on_commit(...)`, so they never fire for rolled-back work and consumers never read uncommitted rows.
   - `select_for_update()` only inside a transaction, on the smallest row set, in a consistent lock order (`mysql-engineering`).
   - Know whether `ATOMIC_REQUESTS` is on; it changes where every view's transaction begins and ends.
5. **Use bulk and update operations knowingly.** `QuerySet.update()`, `bulk_create()` and `bulk_update()` skip `save()`, model signals and `auto_now` updates. Use them only when no business logic depends on those hooks, and set timestamps explicitly. Use `F()` expressions for concurrent counters to avoid lost updates.
6. **Keep signals for decoupled, non-critical reactions.** Business-critical steps belong in explicit service calls, where order and transactions are visible.
7. **DRF**: validate in serializers (`validate_<field>`, `validate`), and keep cross-entity rules in the service; set `permission_classes` explicitly on every view and check object-level permissions (`get_object` + `has_object_permission`) for per-user data; paginate list endpoints; keep error responses consistent with `api-design`.
8. **Security defaults**: never build SQL with string formatting (use the ORM or parameterized `raw()`/`cursor.execute(sql, params)`); avoid `mark_safe` on user data; keep `DEBUG=False`, a proper `ALLOWED_HOSTS`, and the CSRF protections for session-authenticated endpoints; use `sensitive_variables`/`sensitive_post_parameters` where errors could expose secrets (`backend-security`, `logging-security-and-redaction`).
9. **Async**: async views exist from 3.1 and an async ORM interface from 4.1, but calling sync ORM code from async context requires `sync_to_async`. Don't mix without checking the version and the deployment server (ASGI vs WSGI).
10. **Instrument** the operation per `structured-logging-and-instrumentation`; propagate correlation into Celery and queues per `distributed-tracing-and-correlation`.
11. **Test** with the project's runner; use `TestCase` for most tests and `TransactionTestCase` only for real commit behavior (`test-driven-development` references).

## Output

Django code in the project's structure, with service-layer business logic, explicit transaction and side-effect boundaries, query-count-pinned list endpoints, and a note of any version-dependent choice.

## Verification

- [ ] Features used exist in the project's Django/DRF versions.
- [ ] No N+1 in loops or serializers; list endpoints have a query-count assertion.
- [ ] External side effects in write paths run via `transaction.on_commit`.
- [ ] Bulk/update calls don't bypass required business logic; timestamps set explicitly.
- [ ] Every new DRF view declares permissions; per-object access is tested with another user's data.
- [ ] Database invariants are enforced by constraints where data integrity depends on them.
- [ ] Tests, lint and type checks were run; results recorded.

## Escalation

Ask when: a change needs a schema migration on a large or hot table; a business rule currently lives in a signal or `save()` that many paths rely on (moving it is a refactor needing approval); the change alters default permissions or authentication; or async adoption is implied.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Publishing the event right after `save()` is fine." | If the transaction rolls back, consumers act on data that doesn't exist. Use `on_commit`. |
| "`update()` is faster." | It is, and it silently skips `save()`, signals and `auto_now`. |
| "DRF defaults are secure." | The default permission is often `AllowAny` unless the project changed it. Check settings. |

## References

- [references/django-orm-pitfalls.md](references/django-orm-pitfalls.md): N+1 fixes, query-count tests, bulk caveats, locking, on_commit patterns.
- [references/django-version-notes.md](references/django-version-notes.md): features by Django version.

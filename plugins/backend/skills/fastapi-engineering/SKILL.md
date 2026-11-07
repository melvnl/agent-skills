---
name: fastapi-engineering
description: Builds FastAPI services that match the project's FastAPI and Pydantic versions: correct sync vs async endpoints, dependencies for auth and sessions, response models that don't leak fields, consistent error handling, lifespan-managed resources, and durable work kept off BackgroundTasks. Use when working in a FastAPI or Starlette service.
---

# FastAPI Engineering

## Overview

FastAPI is productive, but a few defaults decide whether a service stays healthy under load and doesn't leak data: whether an endpoint blocks the event loop, whether responses are filtered through a model, whether validation errors echo input, and whether "background" work survives a restart. This skill makes those choices explicit and version-correct.

## When to use

- Adding or changing FastAPI routes, dependencies, models, middleware, exception handlers, or startup and shutdown logic.
- Reviewing a FastAPI service for performance, correctness, or data exposure.

**When not to use:** API contract design (resources, errors, versioning, idempotency) → `api-design`. General Python → `python-backend-engineering`.

## Inputs and context

1. **Versions**: FastAPI, Starlette, **Pydantic (v1 or v2: they differ substantially)**, `pydantic-settings`, the ASGI server (Uvicorn, Gunicorn with Uvicorn workers) and Python.
2. **The data access stack**: sync or async DB driver and ORM (SQLAlchemy sync/async, Tortoise, raw drivers), HTTP client (`httpx`, `requests`).
3. **Project structure**: routers, dependency modules, settings, exception handlers, middleware.
4. Auth scheme and where it is enforced.

## Process

1. **Choose `def` or `async def` by what the endpoint calls.**
   - `async def` only if everything it awaits is non-blocking (async DB driver, `httpx.AsyncClient`). One blocking call (sync DB driver, `requests`, `time.sleep`, heavy CPU) inside `async def` stalls **every** request on that worker.
   - Plain `def` endpoints run in a thread pool (AnyIO's default limiter is 40 threads), which is correct for sync drivers, but that pool is a capacity limit to size and monitor.
   - In `async def`, offload unavoidable blocking calls with `starlette.concurrency.run_in_threadpool` or `asyncio.to_thread` (3.9+).
2. **Use dependencies for cross-cutting concerns**: authentication and authorization, DB sessions, settings, the current tenant. Dependencies with `yield` give reliable cleanup (commit or rollback, close). Enforce authorization per route or router, not by convention.
3. **Filter output with response models.** Set `response_model` (or a typed return) to a model that contains only public fields, so internal or sensitive attributes of ORM objects can't leak. Never return ORM objects or dicts built from `__dict__`.
4. **Write version-correct Pydantic.** v2: `model_dump()`, `model_validate()`, `@field_validator`, `@model_validator`, `model_config = ConfigDict(from_attributes=True)`; settings live in the separate `pydantic-settings` package. v1: `.dict()`, `@validator`, `class Config: orm_mode = True`. Don't mix styles; follow the installed major version.
5. **Errors are consistent and safe.** Raise domain exceptions in services and map them to the project's error shape in exception handlers (`api-design`). Override the `RequestValidationError` handler if the default 422 body, which **echoes the invalid input**, could reflect PII or secrets back or into logs.
6. **Manage resources with lifespan.** Create clients and pools in the `lifespan` context manager (FastAPI ≥ 0.93); `@app.on_event("startup")` is deprecated. Close them on shutdown.
7. **Keep durable work off `BackgroundTasks`.** They run in the same process after the response and are lost on crash or deploy. Anything that must happen (decisions, notifications, scoring) goes to a queue (`async-messaging`).
8. **Correlation and logging** via middleware (`distributed-tracing-and-correlation`); access logs may already come from the server; don't duplicate them.
9. **Timeouts everywhere**: outbound clients, DB pools; configure server timeouts behind the load balancer.
10. **Production hygiene**: decide deliberately whether `/docs` and `/openapi.json` are exposed; validate settings at startup; run with the project's worker model.
11. **Test** with `TestClient` or an async client and `app.dependency_overrides`, cleared after each test (`test-driven-development`).

## Output

Routes, dependencies and models consistent with the installed versions, with a note of the sync/async decision for each new endpoint and of anything moved to a queue.

## Verification

- [ ] No blocking call inside `async def` (checked imports and call chains: DB driver, HTTP client, sleeps, CPU-heavy work).
- [ ] Every new route has explicit auth and authorization dependencies, tested with an unauthorized and a cross-user request.
- [ ] Responses go through response models; a test asserts sensitive fields are absent.
- [ ] Pydantic usage matches the installed major version.
- [ ] Validation errors don't echo sensitive input (handler reviewed or tested).
- [ ] Durable work is queued, not in `BackgroundTasks`.
- [ ] Tests, lint and type checks were run; results recorded.

## Escalation

Ask when: the service mixes sync and async data access and the fix implies a driver change; a Pydantic major upgrade is implied; authentication must change; or docs exposure policy is unknown.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "`async def` is faster." | Only when everything awaited is non-blocking. Otherwise it is much slower: the whole worker stalls. |
| "Returning the ORM object is simpler." | Without a response model, every column (password hashes, internal flags) can reach the client. |
| "BackgroundTasks is our queue." | It vanishes on restart. It is a convenience, not a delivery guarantee. |

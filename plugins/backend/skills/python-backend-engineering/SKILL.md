---
name: python-backend-engineering
description: Writes Python backend code that fits the project's actual Python version, tooling and conventions: version-safe syntax, typed boundaries, explicit timeouts, timezone-aware time, Decimal money, correct exception chaining, and I/O kept out of domain logic. Use when writing or changing Python services, libraries, scripts or workers.
---

# Python Backend Engineering

## Overview

Python backend bugs cluster around a few things: features the runtime doesn't have, network calls without timeouts, naive datetimes, float money, swallowed exceptions, and blocking calls inside async code. This skill establishes the project's real constraints first, then applies the practices that prevent those classes of defects. It is the base layer for `django-engineering` and `fastapi-engineering`.

## When to use

- Writing or modifying Python backend code: services, domain logic, API handlers, workers, scripts, libraries.
- Upgrading Python or a core dependency.

**When not to use:** framework-specific concerns → `django-engineering`, `fastapi-engineering`. Query and schema work → `database-design`, `mysql-engineering`. Speed problems → `performance-engineering`.

## Inputs and context

1. **The Python version actually used**, from the strongest evidence: `pyproject.toml` `requires-python`, `.python-version`, `runtime.txt`, the Dockerfile base image, CI matrices, `setup.cfg`/`setup.py` `python_requires`. If they disagree, the deployed runtime wins. Ask if it is unknown.
2. **Tooling in use**: dependency manager (pip-tools, Poetry, uv, Pipenv, plain `requirements.txt`), formatter and linter (Black, Ruff, isort, flake8), type checker (mypy, pyright) and its strictness. Use them; don't introduce alternatives.
3. **Existing conventions**: package layout, error types, config loading, logging, HTTP client, dependency injection style. Read neighboring modules before writing new ones.
4. The Software Factory standards (`.factory/core/CODING_STANDARDS.md`, `ENGINEERING_STANDARDS.md`) when present.

## Process

1. **Fix the language baseline.** Look up what the detected version allows in [references/python-version-matrix.md](references/python-version-matrix.md) before using any newer feature (`X | Y` types, `match`, `list[int]` at runtime, `tomllib`, `ExceptionGroup`, `zoneinfo`). If the project supports several versions, write for the oldest.
2. **Keep domain logic pure.** Business rules are plain functions or classes with no I/O; handlers, jobs and adapters stay thin (factory `ENGINEERING_STANDARDS §2`). This is what makes the rules unit-testable.
3. **Type the boundaries.** Annotate public functions and data crossing modules. Validate untrusted input at the edge with the project's schema library (Pydantic, marshmallow, DRF serializers, dataclasses plus explicit checks). Don't add a validation library the project doesn't use.
4. **Every network call has a timeout.** `requests` has **no default timeout** and will wait forever; pass `timeout=(connect, read)`. Set timeouts for DB, cache, and broker clients too. Retries only for idempotent operations, bounded, with backoff and jitter (`distributed-systems`).
5. **Time is timezone-aware.** Store and compare UTC-aware datetimes (`datetime.now(timezone.utc)`). `datetime.utcnow()` returns a *naive* value and is deprecated since 3.12. Convert to local zones (`zoneinfo`, 3.9+) only at the edges, and only when business rules depend on local dates.
6. **Money is `Decimal`**, never `float` (`money-and-decimal-arithmetic`).
7. **Exceptions carry meaning.** Raise domain-specific exceptions; chain with `raise DomainError(...) from exc`; never `except Exception: pass`. Catch broad exceptions only at a handling boundary that logs once (`structured-logging-and-instrumentation`).
8. **Manage resources** with context managers (files, connections, locks, sessions); don't rely on garbage collection to close them.
9. **Concurrency fits the work.** I/O-bound: threads or `asyncio`. CPU-bound: processes, because the GIL serializes Python bytecode in threads. Never call blocking I/O inside an `async def` without offloading it (`run_in_executor`, `asyncio.to_thread` on 3.9+).
10. **Avoid known traps**: mutable default arguments; module-level state mutated per request; late-binding closures in loops; comparing with `is` for values; implicit string/bytes mixing.
11. **Dependencies.** Add one only with the factory dependency checklist (purpose, maintenance, license, size, removability), using the project's manager and lockfile.
12. **Run the gates** the project defines: formatter, linter, type checker, tests.

## Output

Code consistent with the project's version, tooling and conventions, plus a short note of any version-sensitive choice ("used `Optional[X]`: project supports 3.8").

## Verification

- [ ] Every syntax or library feature used exists in the oldest supported Python version.
- [ ] The project's formatter, linter and type checker pass on changed files (commands and results recorded).
- [ ] All new network calls have timeouts; retries only wrap idempotent calls.
- [ ] No naive datetimes or float money introduced.
- [ ] No swallowed exceptions; chained causes preserved.
- [ ] Domain logic in the change is testable without I/O, and tests were run.

## Escalation

Ask when: the runtime version is unknown or contradictory; the change needs a new dependency or a Python upgrade; or a convention you'd need to break (error handling, config) is load-bearing elsewhere.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Modern syntax is cleaner." | It's a `SyntaxError` on the server running 3.8. Check the version. |
| "The API is fast; no timeout needed." | Until it hangs and exhausts every worker. |
| "`utcnow()` is UTC." | It is naive UTC; comparing it with aware datetimes raises, and mixing them silently corrupts logic. |

## References

- [references/python-version-matrix.md](references/python-version-matrix.md): language and stdlib features by minimum version.

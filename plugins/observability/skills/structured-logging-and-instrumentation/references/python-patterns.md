# Python logging patterns

Use the pattern matching the project's library. Event names, field names and levels follow the project first, these examples second.

## stdlib `logging`

```python
import logging
import time

logger = logging.getLogger(__name__)

def evaluate_eligibility(application, request_id):
    start = time.perf_counter()
    status = "failed"
    try:
        decision = engine.evaluate(application)
        status = "success" if decision.approved else "rejected"
        return decision
    finally:
        logger.info(
            "eligibility_evaluation_completed",
            extra={
                "request_id": request_id,
                "status": status,
                "rule_version": engine.rule_version,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        )
```

Facts that bite:
- `extra` keys must not collide with `LogRecord` attributes (`name`, `msg`, `args`, `levelname`, `module`, `lineno`, `funcName`, `created`, `process`, `thread`, …). `message` and `asctime`, or any existing attribute, raise `KeyError: "Attempt to overwrite ..."`.
- `extra` fields appear in output only if the formatter emits them (a JSON formatter, or a format string naming them).
- Use lazy `%` arguments for variable text in plain-text logs: `logger.debug("cache miss key=%s", key)`. An f-string is formatted even when the level is disabled.
- Guard expensive diagnostics: `if logger.isEnabledFor(logging.DEBUG): logger.debug(...)`.
- `logging.LoggerAdapter` adds context, but before Python 3.13 its default `process()` **replaces** a caller's `extra` with the adapter's own. Python 3.13 added `merge_extra=True`. On older versions, subclass and merge explicitly.
- `stacklevel=` (3.8+) makes a wrapper report the caller's file and line.

## Exceptions

```python
try:
    result = bureau_client.fetch_score(applicant_ref)
except BureauTimeout:
    # Handled here: we fall back, so this layer logs it, once.
    logger.warning(
        "credit_bureau_timeout_fallback",
        extra={"request_id": request_id, "dependency": "credit_bureau", "error_code": "BUREAU_TIMEOUT"},
    )
    result = FALLBACK_SCORE
```

- `logger.exception(...)` logs at ERROR with the traceback; call it only inside `except`, at the layer that handles the error.
- `exc_info=True` attaches the traceback at another level (e.g. WARNING for a recovered but unexpected error).
- Lower layers add context and re-raise (`raise DomainError(...) from exc`) without logging.
- **Exception text can contain data.** Database errors often include the offending value (MySQL `Duplicate entry '<value>' for key ...`); HTTP client errors can include URLs with query strings. Log `error_code` and the exception class name; include the message only when it is known to be safe.

## structlog

```python
import structlog

log = structlog.get_logger(__name__)

def handle(message):
    bound = log.bind(message_id=message.message_id, operation="score_refresh")
    bound.info("message_processing_started")
    ...
    bound.info("message_processing_completed", status="success", duration_ms=elapsed_ms)
```

- Context set with `structlog.contextvars.bind_contextvars(...)` reaches the output only if the configured processor chain includes `structlog.contextvars.merge_contextvars`. Check `structlog.configure(...)` and the installed version before relying on it.
- The first positional argument is the event; keep it a constant snake_case name.

## loguru

```python
from loguru import logger

logger.bind(request_id=request_id).info("eligibility_evaluation_completed status={status}", status="success")
```

Bound values live in `record["extra"]`; structured output requires `serialize=True` or a custom format. Check how the project's sink is configured.

## Durations

Use `time.perf_counter()` or `time.monotonic()`; `time.time()` jumps with clock changes. Report `duration_ms` as a number. Log the duration once, on completion, together with the outcome. Don't log a separate "started" event unless the operation is long-running or its start is itself diagnostic (queue consumers, batch jobs).

## Context in sync vs async code

- Thread-locals work for synchronous WSGI request handling but leak across tasks in `asyncio`.
- `contextvars` (Python 3.7+) work for both threads and asyncio tasks; new tasks copy the current context at creation.
- Celery / thread pools / `run_in_executor` don't automatically carry request context; pass ids explicitly. See `distributed-tracing-and-correlation`.

## Legacy Python

| Feature | Minimum |
|---|---|
| f-strings | 3.6 |
| `contextvars` | 3.7 |
| `logging` `stacklevel` | 3.8 |
| `LoggerAdapter(merge_extra=True)` | 3.13 |

On Python 2.7 or < 3.6, use `%`-style arguments and `extra=`; check `from __future__` usage and the project's support matrix before using newer syntax.

## Asserting logs in tests

```python
def test_completion_event_has_correlation(caplog):
    caplog.set_level(logging.INFO)
    evaluate_eligibility(build_application(), request_id="req-1")
    record = next(r for r in caplog.records if r.getMessage() == "eligibility_evaluation_completed")
    assert record.request_id == "req-1"
    assert record.status in {"success", "rejected"}
    assert not hasattr(record, "national_id")
```

`unittest`: `with self.assertLogs("app.services.eligibility", level="INFO") as cm:`. Assert on fields, not on full formatted strings, so tests survive formatter changes.

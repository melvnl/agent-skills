---
name: structured-logging-and-instrumentation
description: Decides what deserves a log entry and adds concise, structured, correlated, PII-safe logs that reuse the project's existing logger. Use whenever implementing, modifying, or refactoring backend code (endpoints, services, consumers, jobs, external calls), or when asked to add or improve logging.
---

# Structured Logging and Instrumentation

## Overview

Logs exist to answer production questions quickly: what happened to *this* request, *why* did it fail, and *how often*. This skill makes logging a deliberate part of every backend change. It finds the diagnostic boundaries of an operation, adds the few structured events that explain them, and rejects logs that add volume without diagnostic value. The goal is meaningful observability, not maximum log volume.

## When to use

- Implementing, modifying, or refactoring backend functionality: an endpoint, service method, message consumer, background job, external integration, or state transition.
- Asked to "add logging", "improve logs", "make this debuggable", or investigate why an incident was hard to diagnose.

**When not to use:** propagating ids across services or queues → `distributed-tracing-and-correlation`. Deciding whether a field is sensitive → `logging-security-and-redaction`. Designing metrics, traces, dashboards or alerts → `observability-engineering`. Reviewing someone else's diff → `observability-code-review`.

## Inputs and context

Read before writing a single log line:

1. **The existing logging setup.** Follow [references/logger-discovery.md](references/logger-discovery.md): which library (stdlib `logging`, `structlog`, `loguru`, an internal wrapper), how loggers are obtained, which formatter is configured, and how context (request id) is attached today.
2. **The wrapper's implementation, if there is one.** Read its source and two or three real call sites. Never call a method you have not seen defined. Never invent an internal logger API.
3. **The project's conventions:** event naming, field names already in use (`request_id` vs `requestId` vs `x_request_id`), level usage, and any logging section in `CLAUDE.md` or `engineering/DEVELOPMENT_GUIDE.md`.
4. **The runtime:** the Python version (`pyproject.toml`, `setup.cfg`, `.python-version`, `runtime.txt`, Dockerfile) and the logging library version. Don't use `contextvars` (3.7+) or newer `structlog` APIs without confirming they exist.
5. **The operation's execution flow:** entry point, branches, external calls, persistence, async hand-offs, and error paths.
6. **The design's observability plan**, when the Software Factory is used (`specs/<F-ID>-<slug>/DESIGN.md`, section *Observability plan*).

## Process

1. **Map the flow.** List the operation's boundaries: entry, exit, each external dependency call, each state transition, each async hand-off, each error and fallback path.
2. **Run the decision framework** for each candidate event (below). Keep only events that pass it.
3. **Determine correlation context.** Identify the identifiers already available (request id, trace id, message id) and confirm they reach the logs automatically (middleware, contextvars, a bound logger) or must be passed. Cross-boundary propagation belongs to `distributed-tracing-and-correlation`.
4. **Classify every field** you plan to log with `logging-security-and-redaction`. Prefer an allowlist of explicit fields; never log whole objects, request bodies, headers, or ORM instances.
5. **Write the events** in the project's existing style: a constant, short message or event name, and context in structured fields. See [references/python-patterns.md](references/python-patterns.md) for stdlib, `structlog` and wrapper patterns.
6. **Choose the level** with the severity rules below.
7. **Log each exception once**, at the layer that handles it (decides to swallow, convert to a response, retry, or dead-letter). Lower layers add context and re-raise; they don't log and re-raise.
8. **Check volume.** Estimate the rate of each new INFO-or-above event (requests per second × events per request). A success event on a hot path needs a reason; prefer metrics for counts and rates.
9. **Verify the output for real** (see Verification): the formatter actually emits your structured fields, and correlation ids appear.
10. **Report** what was added, where, why, and what was deliberately *not* logged.

### Decision framework

Candidate events (consider each; most changes need only a few):

| # | Event | Usual level |
|---|---|---|
| 1 | Incoming request to an important API (often already logged by middleware: check first) | INFO |
| 2 | Completion of an important operation, with `status` and `duration_ms` | INFO |
| 3 | Authentication / authorization failure | WARNING |
| 4 | Business rule outcome, when operationally relevant (decision made, rule version) | INFO |
| 5 | Important state transition (`from_state`, `to_state`) | INFO |
| 6 | External call failure, timeout, or unusual latency (`dependency`, `duration_ms`) | WARNING / ERROR |
| 7 | Database operation with unusual latency or failure | WARNING / ERROR |
| 8 | Async message consumed (start, with `message_id`) | INFO or DEBUG by volume |
| 9 | Message processing failure | ERROR |
| 10 | Retry attempt / retries exhausted (`retry_count`) | WARNING / ERROR |
| 11 | Background job run (start/end, items processed, duration) | INFO |
| 12 | Configuration or feature-flag change applied at runtime | INFO |
| 13 | Unexpected exception at a handling boundary | ERROR |
| 14 | Critical fallback taken (degraded mode, default decision) | WARNING |
| 15 | Significant operational anomaly (invariant violated, impossible state) | ERROR / CRITICAL |

For every proposed log, answer all seven. A "no" on 1–4 or a "yes" on 5–7 that can't be fixed means **don't add it**:

1. Does it provide diagnostic information someone would actually search for?
2. Is it *not* already observable elsewhere (middleware access log, framework log, APM span, metric)?
3. Does it help correlate or explain a failure?
4. Is the event important enough to retain at its level?
5. Could it expose sensitive information?
6. Is the message unnecessarily verbose?
7. Will it generate excessive volume at production traffic?

### Field conventions

Use the project's existing names first. When none exist, these are the defaults. They are **contextual**: include only fields with diagnostic value for that event.

| Field | Purpose |
|---|---|
| `event` | Stable snake_case name: `eligibility_evaluation_completed` |
| `request_id` | One inbound request |
| `correlation_id` | Related operations across services (reuse the existing id; don't mint a second one) |
| `trace_id`, `span_id` | Distributed trace position (usually injected by tracing instrumentation) |
| `service`, `operation` | Producer and operation (often set once in config or a bound logger) |
| `user_id` | Only an approved internal identifier, and only when safe (`logging-security-and-redaction`) |
| `status` | Outcome: `success`, `rejected`, `failed` |
| `duration_ms` | Measured with a monotonic clock, as a number |
| `error_code` | Stable machine-readable code, not the exception text |
| `retry_count`, `dependency`, `message_id` | Retry behavior, external system, async correlation |

Rules: stable field names (never `amt` in one place and `amount` in another); numbers as numbers; units in the name (`duration_ms`, `size_bytes`); bounded values for anything that becomes a metric label or index.

### Severity

| Level | Use for | Not for |
|---|---|---|
| DEBUG | Detailed diagnostics, normally off in production | Anything needed to investigate an incident |
| INFO | Important lifecycle boundaries and successful completions of important operations | Every function call; every successful query |
| WARNING | Unexpected but recovered conditions: retry, fallback, slow dependency, auth failure | Expected business rejections (an ineligible applicant is INFO with `status=rejected`) |
| ERROR | A failed operation that needs investigation | Validation errors caused by the caller (usually INFO/WARNING, or none) |
| CRITICAL | Service availability or data integrity at risk | Single request failures |

### Volume guards

Never: log every internal function call; log every successful DB query; log entire objects or serialized payloads; log the same exception at several layers; log the same request twice; leave chatty DEBUG on a hot path; use high-cardinality values (user ids, raw URLs with ids) as **metric** labels. Use sampling only for high-volume diagnostic or trace events, **never** for security or audit events.

## Output

1. The code change, matching existing logger conventions.
2. An **instrumentation summary** in the implementation report (or the reply, for small changes):

```markdown
### Instrumentation
| Event | Location | Level | Fields | Why |
|---|---|---|---|---|
| eligibility_evaluation_completed | services/eligibility.py:88 | INFO | request_id, status, rule_version, duration_ms | operation outcome + latency |
Not logged (deliberately): per-rule evaluation steps (high volume, covered by decision record); applicant attributes (PII).
Correlation: request_id via existing middleware; verified in test output.
Unverified: production log pipeline parsing (no access).
```

When no logging is justified, say so and why: "No new logs: the change is internal to a pure function already covered by the caller's completion event."

## Verification

- [ ] Every log call uses an API verified in this codebase (library or wrapper source read).
- [ ] The configured formatter emits the structured fields. Stdlib `logging` with a plain `Formatter` silently drops `extra=` fields; check the handler config or capture output in a test (`caplog`, `assertLogs`).
- [ ] Correlation ids appear in the emitted records (captured in a test or local run).
- [ ] No sensitive fields, payloads, headers, or object dumps (re-checked against `logging-security-and-redaction`).
- [ ] Each exception is logged once; expected rejections are not ERROR.
- [ ] New INFO+ events on hot paths have a volume justification.
- [ ] Tests still pass; any test asserting on logs was run, not assumed.
- [ ] The instrumentation summary lists what was added, what was deliberately omitted, and what could not be verified.

## Escalation

Stop and ask when: the project has no logging convention and the change would establish one (propose it as a decision); logging a field requires a judgment about personal or financial data the policy doesn't cover; a needed correlation id doesn't exist anywhere; the required instrumentation implies a new dependency (a JSON formatter, a tracing SDK); or logs are themselves a compliance artifact (audit). Audit records are not logs: see `financial-auditability`.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "More logs can't hurt." | They cost money, bury the signal, and raise exposure risk. |
| "I'll log the whole request so we have everything." | That is how PII and tokens reach the log platform. Log chosen fields. |
| "Log at each layer to be safe." | Duplicates hide the real origin and multiply volume. Log once where handled. |
| "The logger probably has a `.audit()` method." | Read the source. Invented APIs fail at runtime or silently no-op. |
| "Correlation is handled somewhere." | Prove it: find where the id is bound and see it in output. |

## Red flags

- f-string or `+` concatenation building a message that carries variable data in a structured codebase
- `logger.info(request.data)`, `logger.debug(f"{obj}")`, `extra={"payload": body}`
- `except Exception: logger.error(...); raise` in a layer that doesn't handle the error
- ERROR level for a business "no"
- A new log on a per-item loop at INFO

## References

- [references/logger-discovery.md](references/logger-discovery.md): read first, to identify the logging stack and its conventions.
- [references/python-patterns.md](references/python-patterns.md): read when writing the log calls (stdlib, structlog, wrappers, exceptions, durations, legacy Python).

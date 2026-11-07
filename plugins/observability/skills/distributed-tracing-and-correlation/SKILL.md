---
name: distributed-tracing-and-correlation
description: Preserves request, correlation and trace context across HTTP calls, SQS/SNS messages, background workers and async code, reusing the project's existing identifiers and propagation standard. Use when a change crosses a service, queue, thread or task boundary, or when ids go missing between services.
---

# Distributed Tracing and Correlation

## Overview

A failure in one service is usually caused or felt in another. Correlation identifiers let an engineer follow one business operation through every hop: API, queue, worker, downstream service. This skill keeps those identifiers intact across boundaries with the **fewest** identifiers possible, reusing whatever the project already propagates instead of inventing a parallel scheme.

## When to use

- A change adds or modifies an outbound HTTP call, a message publish or consume (SQS, SNS), a background task (Celery, RQ, cron), a thread pool, or `asyncio` task fan-out.
- Logs for one request can't be joined across services, or a consumer's logs lack the originating request id.
- Introducing or reviewing tracing instrumentation (OpenTelemetry, a vendor APM).

**When not to use:** deciding *which* events to log → `structured-logging-and-instrumentation`. Choosing metrics, dashboards, alerts → `observability-engineering`.

## Inputs and context

1. **Identifiers already in use**: search for `request_id`, `correlation_id`, `trace_id`, `X-Request-ID`, `X-Correlation-ID`, `traceparent`, `AWSTraceHeader` (commands in [references/propagation-patterns.md](references/propagation-patterns.md)). Note each one's origin, header or attribute name, and format.
2. **Tracing stack**: OpenTelemetry SDK, a vendor agent, AWS X-Ray, or none. If present, its context (`trace_id`, `span_id`) is the backbone and other ids must not compete with it.
3. **The boundary types** this change touches: inbound HTTP, outbound HTTP, publish, consume, task enqueue, thread or task spawn.
4. **Runtime**: Python version (`contextvars` needs 3.7; `asyncio.to_thread` needs 3.9), sync (WSGI) vs async (ASGI), worker framework and version.
5. Platform conventions documented in `CLAUDE.md` or `engineering/` (required headers, attribute names).

## Process

1. **Fix the identifier set.** Use the decision table below. Record the result in the design's *Observability plan* (Software Factory) or the change description.
2. **Ingress.** At each entry point (HTTP middleware, message consumer, job runner): read the incoming id if present and **valid**, otherwise generate one. Validate inbound values: bounded length (e.g. ≤ 128), restricted charset (`[A-Za-z0-9._:-]`). Untrusted ids that fail validation are replaced, not logged raw: this prevents log injection.
3. **Hold context in-process** with the project's mechanism: `contextvars` for async or mixed code, thread-locals only in purely synchronous WSGI code, or the tracing SDK's context. Make logging read from it (filter, processor, bound logger) so call sites don't pass ids by hand.
4. **Egress.** On every outbound call, inject the same ids: HTTP headers; SQS/SNS `MessageAttributes`; task headers or kwargs. With OpenTelemetry, use its propagator (`inject`/`extract`) rather than hand-written `traceparent`.
5. **Cross execution boundaries explicitly.** New `asyncio` tasks copy the current context automatically. `loop.run_in_executor` and `ThreadPoolExecutor.submit` do **not**: wrap the callable with `contextvars.copy_context().run`, or use `asyncio.to_thread` (3.9+, copies context). Celery and other brokers never inherit context: put ids in the task message.
6. **Model spans correctly**, when tracing exists: synchronous calls are child spans; a message consumer's span is a child of, or **linked** to, the producer's span. Batch consumers use span links, one per message, because one span can't have many parents.
7. **Identify the service and operation** once (service name from config, e.g. `OTEL_SERVICE_NAME`), not per log call.
8. **Echo the id back** to callers where useful (response header `X-Request-ID`), so support tickets can quote it.
9. **Test propagation** across at least one boundary of each type you touched (Verification).

### Identifier decision table

| Situation | Use |
|---|---|
| Tracing (OTel/APM) is installed and propagated end to end | `trace_id` / `span_id` as the correlation backbone; keep an existing `request_id` for per-request lookup; **don't add** a separate `correlation_id` |
| No tracing; ids already propagated (`X-Request-ID`, `X-Correlation-ID`) | Reuse those exact names and formats everywhere |
| No tracing, nothing propagated | Introduce **one** id at the edge (`correlation_id`, or the platform's standard name) and propagate it; propose tracing as a separate decision |
| Async message processing | Add `message_id` (the broker's id, per delivery) **alongside** the propagated correlation id; it identifies the delivery, not the business operation |
| Retries and redeliveries | Same correlation id; increment `retry_count`; the broker's receive count (SQS `ApproximateReceiveCount`) shows redelivery |

Never mint a new correlation id mid-flow because one "wasn't handy": that splits the operation into two unjoinable halves.

### SQS and SNS specifics

- SQS allows at most **10 message attributes** per message; budget them (e.g. `traceparent`, `correlation_id`).
- AWS X-Ray uses the SQS **system** attribute `AWSTraceHeader`, separate from message attributes.
- SNS → SQS: with **raw message delivery off**, SNS wraps the message in a JSON envelope and the attributes are inside the envelope's `MessageAttributes`. With raw delivery **on**, they arrive as SQS message attributes. The consumer must handle the mode actually configured.
- Producers that publish many messages from one request propagate the same correlation id on each.

Code patterns: [references/propagation-patterns.md](references/propagation-patterns.md).

## Output

1. The propagation change (middleware, injection, extraction, executor wrapping), using existing mechanisms.
2. A **correlation map** in the design or implementation report:

```markdown
### Correlation
| Boundary | Carrier | Ids | Mechanism | Verified by |
|---|---|---|---|---|
| Client -> API | header X-Request-ID | request_id | existing middleware | test_request_id_roundtrip |
| API -> SQS score-refresh | MessageAttributes | correlation_id, traceparent | otel inject | test_publish_injects_context |
| SQS -> worker | MessageAttributes | correlation_id, message_id | consumer extract + bind | test_consumer_binds_context |
Gaps: legacy batch job (no context; follow-up T-14).
```

## Verification

- [ ] For each boundary touched, a test (or local run) shows the id leaving one side and arriving on the other: captured HTTP headers, the published message attributes, and the consumer's log record or span.
- [ ] Ingress validation tested with a missing, a valid, and a malformed inbound id.
- [ ] Executor and thread hand-offs keep context (test reads the contextvar inside the worker callable).
- [ ] No new identifier duplicates an existing one's purpose.
- [ ] SQS attribute count stays within the limit; the SNS raw-delivery mode is handled as configured.
- [ ] Correlation map written, gaps listed.

## Escalation

Ask when: two incompatible id schemes already exist (choosing one is a platform decision); adding tracing requires a new SDK or agent (dependency + cost decision); propagation would cross a trust boundary to a third party (don't leak internal ids externally without approval); or the queue's attribute budget is exhausted.

## Red flags

- `uuid4()` generated inside a service layer or consumer instead of at ingress
- Outbound `requests`/`httpx` calls without the project's header injection
- `executor.submit(fn)` in request code that logs, with no context copy
- A consumer that logs only `message_id` and drops the producer's correlation id
- Different header names for the same id in different services

## References

- [references/propagation-patterns.md](references/propagation-patterns.md): read when implementing ingress, HTTP egress, SQS/SNS publish and consume, Celery, or executor propagation.
